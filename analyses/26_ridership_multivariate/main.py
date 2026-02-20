"""Analysis 26: Test whether ridership adds explanatory power to the Analysis 18 multivariate OTP model."""

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


# ---------------------------------------------------------------------------
# Helpers (replicated from Analysis 18 to maintain independence)
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

    # Standardized beta weights
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
    """Assemble all features including ridership for the regression model."""
    # Route-level average OTP (from paired months only)
    avg_otp = query_to_polars("""
        SELECT o.route_id, rt.route_name, rt.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        JOIN routes rt ON o.route_id = rt.route_id
        WHERE r.avg_riders IS NOT NULL
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)

    # Average weekday ridership
    avg_riders = query_to_polars("""
        SELECT route_id, AVG(avg_riders) AS avg_riders
        FROM ridership_monthly
        WHERE day_type = 'WEEKDAY' AND avg_riders IS NOT NULL
        GROUP BY route_id
    """)

    # Structural features
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

    # Assemble
    df = avg_otp
    df = df.join(avg_riders, on="route_id", how="inner")
    df = df.join(stop_counts, on="route_id", how="left")
    df = df.join(trips, on="route_id", how="left")
    df = df.join(munis, on="route_id", how="left")
    df = df.join(span_df, on="route_id", how="left")

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
        pl.col("avg_riders").log().alias("log_riders"),
    )

    df = df.drop_nulls(subset=["stop_count", "span_km", "weekend_ratio", "n_munis", "avg_riders"])

    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_coefficient_chart(base: dict, expanded: dict) -> None:
    """Compare standardized coefficients between base and expanded models."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    # Get shared features (skip intercept)
    base_feats = base["features"][1:]
    exp_feats = expanded["features"][1:]
    base_betas = {f: b for f, b in zip(base_feats, base["beta_weights"][1:])}
    exp_betas = {f: b for f, b in zip(exp_feats, expanded["beta_weights"][1:])}
    exp_pvals = {f: p for f, p in zip(exp_feats, expanded["p_values"][1:])}

    all_feats = exp_feats  # expanded has all features
    y_pos = np.arange(len(all_feats))
    width = 0.35

    base_vals = [base_betas.get(f, 0.0) for f in all_feats]
    exp_vals = [exp_betas[f] for f in all_feats]

    bars1 = ax.barh(y_pos + width / 2, base_vals, width, label="Base (6 features)",
                     color="#9ca3af", alpha=0.7)
    bars2 = ax.barh(y_pos - width / 2, exp_vals, width, label="Expanded (+ridership)",
                     color="#2563eb", alpha=0.7)

    # Significance markers for expanded model
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
    """Partial residual plot: base model residuals vs log_riders."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    residuals = base["residuals"]
    log_riders = df["log_riders"].to_numpy()

    ax.scatter(log_riders, residuals, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)

    # Trend line
    slope, intercept, r, p, _ = stats.linregress(log_riders, residuals)
    x_line = np.array([log_riders.min(), log_riders.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Log(Average Weekday Ridership)")
    ax.set_ylabel("Base Model Residual (OTP)")
    ax.set_title("Partial Residual: Does Ridership Explain Remaining OTP Variance?")
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
    print("Analysis 26: Ridership in Multivariate OTP Model")
    print("=" * 60)

    print("\nLoading and assembling features...")
    df = load_features()
    n_rail = len(df.filter(pl.col("is_rail") == 1.0))
    n_bus = len(df.filter(pl.col("mode") == "BUS"))
    print(f"  {len(df)} routes with complete feature set ({n_bus} BUS, {n_rail} RAIL)")
    print(f"  Ridership range: {df['avg_riders'].min():.0f} -- {df['avg_riders'].max():.0f}")
    print(f"  Log ridership range: {df['log_riders'].min():.2f} -- {df['log_riders'].max():.2f}")

    y = df["avg_otp"].to_numpy()

    # --- Model 1: Base (Analysis 18 replication, 6 features) ---
    base_features = ["stop_count", "span_km", "is_rail", "is_premium_bus",
                     "weekend_ratio", "n_munis"]
    X_base = np.column_stack([df[f].to_numpy().astype(float) for f in base_features])
    print("\nFitting base model (6 features, Analysis 18 replication)...")
    base = fit_ols(y, X_base, base_features)
    print_model(base, "Base model (6 features)")

    # --- Model 2: Expanded (+ log_riders) ---
    exp_features = base_features + ["log_riders"]
    X_exp = np.column_stack([df[f].to_numpy().astype(float) for f in exp_features])
    print("\nFitting expanded model (+ log_riders)...")
    expanded = fit_ols(y, X_exp, exp_features)
    print_model(expanded, "Expanded model (+ log_riders)")

    # F-test
    f_stat, f_p = f_test_nested(base, expanded)
    print(f"\n  F-test for log_riders: F = {f_stat:.3f}, p = {f_p:.4f}")
    print(f"  R2 change: {base['r_squared']:.4f} -> {expanded['r_squared']:.4f} "
          f"(+{expanded['r_squared'] - base['r_squared']:.4f})")
    print(f"  Adj R2 change: {base['adj_r_squared']:.4f} -> {expanded['adj_r_squared']:.4f} "
          f"(+{expanded['adj_r_squared'] - base['adj_r_squared']:.4f})")
    if f_p < 0.05:
        print("  => Ridership IS significant after controlling for structural features.")
    else:
        print("  => Ridership is NOT significant after controlling for structural features.")

    # --- VIF for expanded model ---
    print("\n--- VIF (Expanded Model) ---")
    vifs = compute_vif(X_exp, exp_features)
    for feat, vif in vifs.items():
        flag = " ** HIGH" if vif > 5 else ""
        print(f"  {feat:<20s} VIF = {vif:.2f}{flag}")

    # --- Model 3: Ridership-only (log_riders + is_rail) ---
    rider_features = ["log_riders", "is_rail"]
    X_rider = np.column_stack([df[f].to_numpy().astype(float) for f in rider_features])
    print("\nFitting ridership-only model (log_riders + is_rail)...")
    rider_only = fit_ols(y, X_rider, rider_features)
    print_model(rider_only, "Ridership-only model")

    # --- Model 4: Bus-only expanded ---
    bus_df = df.filter(pl.col("mode") == "BUS")
    y_bus = bus_df["avg_otp"].to_numpy()
    bus_base_feats = ["stop_count", "span_km", "is_premium_bus", "weekend_ratio", "n_munis"]
    bus_exp_feats = bus_base_feats + ["log_riders"]

    X_bus_base = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_base_feats])
    X_bus_exp = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_exp_feats])

    print(f"\nFitting bus-only base model ({len(bus_df)} routes)...")
    bus_base = fit_ols(y_bus, X_bus_base, bus_base_feats)
    print_model(bus_base, "Bus-only base (5 features)")

    print(f"\nFitting bus-only expanded model (+ log_riders)...")
    bus_expanded = fit_ols(y_bus, X_bus_exp, bus_exp_feats)
    print_model(bus_expanded, "Bus-only expanded (+ log_riders)")

    f_bus, fp_bus = f_test_nested(bus_base, bus_expanded)
    print(f"\n  Bus-only F-test for log_riders: F = {f_bus:.3f}, p = {fp_bus:.4f}")
    print(f"  R2 change: {bus_base['r_squared']:.4f} -> {bus_expanded['r_squared']:.4f} "
          f"(+{bus_expanded['r_squared'] - bus_base['r_squared']:.4f})")

    # --- Correlation between ridership and existing predictors ---
    print("\n--- Correlations: log_riders vs structural features ---")
    for feat in base_features:
        r, p = stats.pearsonr(df[feat].to_numpy().astype(float), df["log_riders"].to_numpy())
        sig = "*" if p < 0.05 else ""
        print(f"  log_riders vs {feat:<20s}: r = {r:+.3f}, p = {p:.4f} {sig}")

    # --- Save outputs ---
    print("\nSaving CSVs...")

    # Model comparison
    rows = []
    for model, label in [(base, "base_6feat"), (expanded, "expanded_7feat"),
                          (rider_only, "ridership_only"), (bus_base, "bus_base"),
                          (bus_expanded, "bus_expanded")]:
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

    print("\nGenerating charts...")
    make_coefficient_chart(base, expanded)
    make_partial_residual_chart(df, base)

    print("\nDone.")


if __name__ == "__main__":
    main()
