"""Analysis 27: Test whether PennDOT AADT traffic volume explains OTP variance beyond structural features."""

import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    classify_bus_route,
    output_dir,
    query_to_polars,
    setup_plotting,
)

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12
MIN_MATCH_RATE = 0.3


# ---------------------------------------------------------------------------
# Helpers (replicated from Analysis 18/26 to maintain independence)
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_span(lats: list[float], lons: list[float]) -> float:
    """Return the max pairwise haversine distance (km) among a set of points."""
    max_dist = 0.0
    n = len(lats)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(lats[i], lons[i], lats[j], lons[j])
            if d > max_dist:
                max_dist = d
    return max_dist


def compute_vif(X_raw: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """Compute Variance Inflation Factor for each predictor."""
    n, k = X_raw.shape
    vifs = {}
    for j in range(k):
        y_j = X_raw[:, j]
        X_other = np.delete(X_raw, j, axis=1)
        X_other = np.column_stack([np.ones(n), X_other])
        beta, _, _, _ = np.linalg.lstsq(X_other, y_j, rcond=None)
        y_hat = X_other @ beta
        ss_res = np.sum((y_j - y_hat) ** 2)
        ss_tot = np.sum((y_j - np.mean(y_j)) ** 2)
        r2_j = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        vifs[feature_names[j]] = 1.0 / (1.0 - r2_j) if r2_j < 1.0 else float("inf")
    return vifs


def fit_ols(y: np.ndarray, X_raw: np.ndarray, feature_names: list[str]) -> dict:
    """Fit OLS regression and return results dict."""
    n, k = X_raw.shape
    X = np.column_stack([np.ones(n), X_raw])

    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    residuals = y - y_hat

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
    mse = ss_res / (n - k - 1)

    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(XtX_inv) * mse)
    t_vals = beta / se
    p_vals = [2 * (1 - stats.t.cdf(abs(t), df=n - k - 1)) for t in t_vals]

    x_stds = np.std(X_raw, axis=0, ddof=1)
    y_std = np.std(y, ddof=1)
    beta_weights = beta[1:] * x_stds / y_std

    return {
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "ss_res": ss_res,
        "n": n,
        "k": k,
        "features": ["intercept"] + feature_names,
        "coefficients": beta.tolist(),
        "std_errors": se.tolist(),
        "t_values": t_vals.tolist(),
        "p_values": p_vals,
        "beta_weights": [None] + beta_weights.tolist(),
        "y_hat": y_hat,
        "residuals": residuals,
    }


def f_test_nested(base: dict, full: dict) -> tuple[float, float]:
    """F-test comparing nested models. Returns (F_stat, p_value)."""
    k_diff = full["k"] - base["k"]
    n = full["n"]
    f_stat = ((base["ss_res"] - full["ss_res"]) / k_diff) / (full["ss_res"] / (n - full["k"] - 1))
    f_p = 1 - stats.f.cdf(f_stat, k_diff, n - full["k"] - 1)
    return f_stat, f_p


def print_model(results: dict, label: str) -> None:
    """Print formatted model results."""
    print(f"\n  {label}:")
    print(f"  R2 = {results['r_squared']:.4f}, Adj R2 = {results['adj_r_squared']:.4f}, "
          f"n = {results['n']}, k = {results['k']}")
    print(f"  {'Feature':<20s} {'Coeff':>10s} {'Std Err':>10s} {'p-value':>10s} {'Beta':>10s}")
    print(f"  {'-'*60}")
    for i, feat in enumerate(results["features"]):
        coeff = results["coefficients"][i]
        se = results["std_errors"][i]
        p = results["p_values"][i]
        beta = results["beta_weights"][i]
        beta_str = f"{beta:>10.4f}" if beta is not None else f"{'--':>10s}"
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        print(f"  {feat:<20s} {coeff:>10.6f} {se:>10.6f} {p:>10.4f} {beta_str} {sig}")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_features() -> pl.DataFrame:
    """Assemble structural features + traffic data for the regression model."""
    avg_otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)

    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops GROUP BY route_id
    """)
    trips = query_to_polars("""
        SELECT route_id,
               MAX(trips_wd) AS max_wd,
               MAX(trips_sa) AS max_sa,
               MAX(trips_su) AS max_su
        FROM route_stops GROUP BY route_id
    """)
    munis = query_to_polars("""
        SELECT rs.route_id, COUNT(DISTINCT s.muni) AS n_munis
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.muni IS NOT NULL AND s.muni != '0'
        GROUP BY rs.route_id
    """)
    stops_by_route = query_to_polars("""
        SELECT rs.route_id, s.lat, s.lon
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.lat IS NOT NULL AND s.lon IS NOT NULL
    """)
    spans = []
    for route_id in stops_by_route["route_id"].unique().sort().to_list():
        subset = stops_by_route.filter(pl.col("route_id") == route_id)
        span_km = compute_span(subset["lat"].to_list(), subset["lon"].to_list())
        spans.append({"route_id": route_id, "span_km": span_km})
    span_df = pl.DataFrame(spans)

    # Traffic data
    traffic = query_to_polars("""
        SELECT route_id, weighted_aadt, max_aadt, median_aadt, p90_aadt,
               avg_truck_pct, match_rate, n_segments, total_length_ft
        FROM route_traffic
    """)

    # Assemble
    df = avg_otp
    df = df.join(stop_counts, on="route_id", how="left")
    df = df.join(trips, on="route_id", how="left")
    df = df.join(munis, on="route_id", how="left")
    df = df.join(span_df, on="route_id", how="left")
    df = df.join(traffic, on="route_id", how="inner")

    # Derived features
    df = df.with_columns(
        pl.when(pl.col("max_wd") > 0)
        .then((pl.col("max_sa") + pl.col("max_su")) / (2.0 * pl.col("max_wd")))
        .otherwise(0.0)
        .alias("weekend_ratio"),
    )
    df = df.with_columns(
        pl.when(pl.col("mode") == "RAIL").then(1.0).otherwise(0.0).alias("is_rail"),
    )
    df = df.with_columns(
        pl.when(pl.col("mode") == "BUS")
        .then(pl.col("route_id").map_elements(classify_bus_route, return_dtype=pl.Utf8))
        .otherwise(pl.lit("non_bus"))
        .alias("bus_subtype"),
    )
    df = df.with_columns(
        pl.when(pl.col("bus_subtype").is_in(["busway", "flyer", "express", "limited"]))
        .then(1.0)
        .otherwise(0.0)
        .alias("is_premium_bus"),
    )
    df = df.with_columns(
        pl.col("weighted_aadt").log().alias("log_aadt"),
    )

    df = df.drop_nulls(subset=["stop_count", "span_km", "weekend_ratio", "n_munis"])

    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_scatter_chart(df: pl.DataFrame) -> None:
    """Bivariate scatter: AADT vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    aadt = df["weighted_aadt"].to_numpy()
    otp = df["avg_otp"].to_numpy()
    modes = df["mode"].to_list()

    bus_mask = np.array([m == "BUS" for m in modes])
    rail_mask = ~bus_mask

    ax.scatter(aadt[bus_mask], otp[bus_mask], alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5, label="Bus", zorder=2)
    if np.any(rail_mask):
        ax.scatter(aadt[rail_mask], otp[rail_mask], alpha=0.7, s=50, color="#dc2626",
                   marker="D", edgecolors="white", linewidth=0.5, label="Rail", zorder=3)

    # Trend line (all routes)
    log_aadt = np.log(aadt)
    slope, intercept, r, p, _ = stats.linregress(log_aadt, otp)
    x_sorted = np.sort(aadt)
    ax.plot(x_sorted, slope * np.log(x_sorted) + intercept, color="#e11d48",
            linewidth=1.5, linestyle="--", alpha=0.7,
            label=f"log fit: r={r:.3f}, p={p:.4f}")

    ax.set_xlabel("Weighted AADT (vehicles/day)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Traffic Volume vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_xscale("log")

    fig.tight_layout()
    fig.savefig(OUT / "aadt_vs_otp_scatter.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'aadt_vs_otp_scatter.png'}")


def make_coefficient_chart(base: dict, expanded: dict) -> None:
    """Compare standardized coefficients between base and expanded models."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    base_feats = base["features"][1:]
    exp_feats = expanded["features"][1:]
    base_betas = {f: b for f, b in zip(base_feats, base["beta_weights"][1:])}
    exp_betas = {f: b for f, b in zip(exp_feats, expanded["beta_weights"][1:])}
    exp_pvals = {f: p for f, p in zip(exp_feats, expanded["p_values"][1:])}

    all_feats = exp_feats
    y_pos = np.arange(len(all_feats))
    width = 0.35

    base_vals = [base_betas.get(f, 0.0) for f in all_feats]
    exp_vals = [exp_betas[f] for f in all_feats]

    ax.barh(y_pos + width / 2, base_vals, width, label="Base (6 features)",
            color="#9ca3af", alpha=0.7)
    ax.barh(y_pos - width / 2, exp_vals, width, label="Expanded (+log_aadt)",
            color="#2563eb", alpha=0.7)

    for i, f in enumerate(all_feats):
        p = exp_pvals[f]
        marker = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        val = exp_vals[i]
        ax.text(val + 0.01 if val >= 0 else val - 0.01, i - width / 2, marker,
                ha="left" if val >= 0 else "right", va="center", fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(all_feats)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Standardized Coefficient (Beta Weight)")
    ax.set_title(f"Model Comparison: Base R2={base['r_squared']:.3f} vs "
                 f"Expanded R2={expanded['r_squared']:.3f}")
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(OUT / "coefficient_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'coefficient_comparison.png'}")


def make_partial_residual_chart(df: pl.DataFrame, base: dict) -> None:
    """Partial residual plot: base model residuals vs log_aadt."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    residuals = base["residuals"]
    log_aadt = df["log_aadt"].to_numpy()

    ax.scatter(log_aadt, residuals, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)

    slope, intercept, r, p, _ = stats.linregress(log_aadt, residuals)
    x_line = np.array([log_aadt.min(), log_aadt.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Log(Weighted AADT)")
    ax.set_ylabel("Base Model Residual (OTP)")
    ax.set_title("Partial Residual: Does Traffic Volume Explain Remaining OTP Variance?")
    ax.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT / "partial_residual.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'partial_residual.png'}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: load features, fit models, compare, chart, and save."""
    print("=" * 60)
    print("Analysis 27: Traffic Congestion and OTP")
    print("=" * 60)

    print("\nLoading and assembling features...")
    df_all = load_features()
    print(f"  {len(df_all)} routes with traffic + structural features")

    # Filter by match rate
    df = df_all.filter(pl.col("match_rate") >= MIN_MATCH_RATE)
    excluded = df_all.filter(pl.col("match_rate") < MIN_MATCH_RATE)
    n_rail = len(df.filter(pl.col("is_rail") == 1.0))
    n_bus = len(df.filter(pl.col("mode") == "BUS"))
    print(f"  {len(df)} routes after match_rate >= {MIN_MATCH_RATE} filter ({n_bus} BUS, {n_rail} RAIL)")
    if len(excluded) > 0:
        print(f"  Excluded ({len(excluded)}): "
              + ", ".join(excluded.sort("match_rate")["route_id"].to_list()))

    print(f"\n  AADT range: {df['weighted_aadt'].min():,.0f} -- {df['weighted_aadt'].max():,.0f}")
    print(f"  Log AADT range: {df['log_aadt'].min():.2f} -- {df['log_aadt'].max():.2f}")
    print(f"  Median match rate: {df['match_rate'].median():.1%}")

    y = df["avg_otp"].to_numpy()

    # --- Model 1: Base (Analysis 18 replication, 6 features) ---
    base_features = ["stop_count", "span_km", "is_rail", "is_premium_bus",
                     "weekend_ratio", "n_munis"]
    X_base = np.column_stack([df[f].to_numpy().astype(float) for f in base_features])
    print("\nFitting base model (6 features, Analysis 18 replication)...")
    base = fit_ols(y, X_base, base_features)
    print_model(base, "Base model (6 features)")

    # --- Model 2: Expanded (+ log_aadt) ---
    exp_features = base_features + ["log_aadt"]
    X_exp = np.column_stack([df[f].to_numpy().astype(float) for f in exp_features])
    print("\nFitting expanded model (+ log_aadt)...")
    expanded = fit_ols(y, X_exp, exp_features)
    print_model(expanded, "Expanded model (+ log_aadt)")

    # F-test
    f_stat, f_p = f_test_nested(base, expanded)
    print(f"\n  F-test for log_aadt: F = {f_stat:.3f}, p = {f_p:.4f}")
    print(f"  R2 change: {base['r_squared']:.4f} -> {expanded['r_squared']:.4f} "
          f"(+{expanded['r_squared'] - base['r_squared']:.4f})")
    print(f"  Adj R2 change: {base['adj_r_squared']:.4f} -> {expanded['adj_r_squared']:.4f} "
          f"(+{expanded['adj_r_squared'] - base['adj_r_squared']:.4f})")
    if f_p < 0.05:
        print("  => AADT IS significant after controlling for structural features.")
    else:
        print("  => AADT is NOT significant after controlling for structural features.")

    # --- Model 3: Expanded + truck_pct ---
    truck_df = df.filter(pl.col("avg_truck_pct").is_not_null())
    if len(truck_df) >= 20:
        y_truck = truck_df["avg_otp"].to_numpy()
        truck_features = base_features + ["log_aadt", "avg_truck_pct"]
        X_truck = np.column_stack([truck_df[f].to_numpy().astype(float) for f in truck_features])
        print(f"\nFitting expanded model (+ log_aadt + avg_truck_pct, n={len(truck_df)})...")
        truck_model = fit_ols(y_truck, X_truck, truck_features)
        print_model(truck_model, "Expanded model (+ log_aadt + avg_truck_pct)")

        # Compare vs base on same sample
        X_base_truck = np.column_stack([truck_df[f].to_numpy().astype(float) for f in base_features])
        base_truck = fit_ols(y_truck, X_base_truck, base_features)
        f2, fp2 = f_test_nested(base_truck, truck_model)
        print(f"\n  F-test for log_aadt + truck_pct (joint): F = {f2:.3f}, p = {fp2:.4f}")
    else:
        truck_model = None
        print(f"\n  Skipping truck_pct model (only {len(truck_df)} routes with truck data)")

    # --- VIF for expanded model ---
    print("\n--- VIF (Expanded Model: base + log_aadt) ---")
    vifs = compute_vif(X_exp, exp_features)
    for feat, vif in vifs.items():
        flag = " ** HIGH" if vif > 5 else ""
        print(f"  {feat:<20s} VIF = {vif:.2f}{flag}")

    # --- Correlation: log_aadt vs structural features ---
    print("\n--- Correlations: log_aadt vs structural features ---")
    for feat in base_features:
        r, p = stats.pearsonr(df[feat].to_numpy().astype(float), df["log_aadt"].to_numpy())
        sig = "*" if p < 0.05 else ""
        print(f"  log_aadt vs {feat:<20s}: r = {r:+.3f}, p = {p:.4f} {sig}")

    # --- Bus-only subgroup ---
    bus_df = df.filter(pl.col("mode") == "BUS")
    y_bus = bus_df["avg_otp"].to_numpy()
    bus_base_feats = ["stop_count", "span_km", "is_premium_bus", "weekend_ratio", "n_munis"]
    bus_exp_feats = bus_base_feats + ["log_aadt"]

    X_bus_base = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_base_feats])
    X_bus_exp = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_exp_feats])

    print(f"\nFitting bus-only base model ({len(bus_df)} routes)...")
    bus_base = fit_ols(y_bus, X_bus_base, bus_base_feats)
    print_model(bus_base, "Bus-only base (5 features)")

    print(f"\nFitting bus-only expanded model (+ log_aadt)...")
    bus_expanded = fit_ols(y_bus, X_bus_exp, bus_exp_feats)
    print_model(bus_expanded, "Bus-only expanded (+ log_aadt)")

    f_bus, fp_bus = f_test_nested(bus_base, bus_expanded)
    print(f"\n  Bus-only F-test for log_aadt: F = {f_bus:.3f}, p = {fp_bus:.4f}")
    print(f"  R2 change: {bus_base['r_squared']:.4f} -> {bus_expanded['r_squared']:.4f} "
          f"(+{bus_expanded['r_squared'] - bus_base['r_squared']:.4f})")

    # --- Save outputs ---
    print("\nSaving CSVs...")

    # Model comparison
    rows = []
    models = [
        (base, "base_6feat"),
        (expanded, "expanded_7feat_aadt"),
        (bus_base, "bus_base"),
        (bus_expanded, "bus_expanded_aadt"),
    ]
    if truck_model is not None:
        models.append((truck_model, "expanded_8feat_aadt_truck"))
    for model, label in models:
        for i, feat in enumerate(model["features"]):
            rows.append({
                "model": label,
                "feature": feat,
                "coefficient": model["coefficients"][i],
                "std_error": model["std_errors"][i],
                "p_value": model["p_values"][i],
                "beta_weight": model["beta_weights"][i] if model["beta_weights"][i] is not None else float("nan"),
                "r_squared": model["r_squared"],
                "adj_r_squared": model["adj_r_squared"],
                "n": model["n"],
            })
    pl.DataFrame(rows).write_csv(OUT / "model_comparison.csv")
    print(f"  {OUT / 'model_comparison.csv'}")

    # VIF table
    vif_rows = [{"feature": f, "vif": v} for f, v in vifs.items()]
    pl.DataFrame(vif_rows).write_csv(OUT / "vif_table.csv")
    print(f"  {OUT / 'vif_table.csv'}")

    # Route-level summary
    summary = df.select([
        "route_id", "route_name", "mode", "avg_otp", "weighted_aadt", "max_aadt",
        "median_aadt", "p90_aadt", "avg_truck_pct", "match_rate", "n_segments",
        "stop_count", "span_km",
    ]).sort("weighted_aadt", descending=True)
    summary.write_csv(OUT / "route_traffic_summary.csv")
    print(f"  {OUT / 'route_traffic_summary.csv'}")

    print("\nGenerating charts...")
    make_scatter_chart(df)
    make_coefficient_chart(base, expanded)
    make_partial_residual_chart(df, base)

    print("\nDone.")


if __name__ == "__main__":
    main()
