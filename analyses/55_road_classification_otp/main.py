"""Analysis 55: Test whether road type (lanes, functional class, speed) explains OTP beyond structural features."""

import math

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    analysis_dir,
    classify_bus_route,
    correlate,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.common.schemas import ROUTE_ROAD_CLASS, validate

OUT = analysis_dir(__file__)

MIN_MONTHS = 12
MIN_MATCH_RATE = 0.3

ROAD_FEATURES = ["weighted_lanes", "weighted_func_cls", "weighted_speed"]


# ---------------------------------------------------------------------------
# Helpers (replicated from Analysis 18/27 to keep analyses independent)
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
    """Assemble structural features + road-classification data for the regression model."""
    avg_otp_df = query_to_polars(f"""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= {MIN_MONTHS}
    """)

    stop_counts_df = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops GROUP BY route_id
    """)
    trips_df = query_to_polars("""
        SELECT route_id,
               MAX(trips_wd) AS max_wd,
               MAX(trips_sa) AS max_sa,
               MAX(trips_su) AS max_su
        FROM route_stops GROUP BY route_id
    """)
    munis_df = query_to_polars("""
        SELECT rs.route_id, COUNT(DISTINCT s.muni) AS n_munis
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.muni IS NOT NULL AND s.muni != '0'
        GROUP BY rs.route_id
    """)
    stops_by_route_df = query_to_polars("""
        SELECT rs.route_id, s.lat, s.lon
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.lat IS NOT NULL AND s.lon IS NOT NULL
    """)
    spans = []
    for route_id in stops_by_route_df["route_id"].unique().sort().to_list():
        subset = stops_by_route_df.filter(pl.col("route_id") == route_id)
        span_km = compute_span(subset["lat"].to_list(), subset["lon"].to_list())
        spans.append({"route_id": route_id, "span_km": span_km})
    span_df = pl.DataFrame(spans)

    road_df = query_to_polars("""
        SELECT route_id, weighted_lanes, weighted_func_cls, weighted_speed,
               arterial_share, divided_share, match_rate, n_segments, total_length_ft
        FROM route_road_class
    """)
    validate(road_df, ROUTE_ROAD_CLASS, subset=True)

    truck_df = query_to_polars("SELECT route_id, avg_truck_pct FROM route_traffic")

    df = avg_otp_df
    df = df.join(stop_counts_df, on="route_id", how="left")
    df = df.join(trips_df, on="route_id", how="left")
    df = df.join(munis_df, on="route_id", how="left")
    df = df.join(span_df, on="route_id", how="left")
    df = df.join(road_df, on="route_id", how="inner")
    df = df.join(truck_df, on="route_id", how="left")

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

    # Road-type features and the structural baseline must be present.
    df = df.drop_nulls(subset=["stop_count", "span_km", "weekend_ratio", "n_munis"] + ROAD_FEATURES)

    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_lanes_scatter(df: pl.DataFrame) -> None:
    """Bivariate scatter: lane count vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    lanes = df["weighted_lanes"].to_numpy()
    otp = df["avg_otp"].to_numpy()
    modes = df["mode"].to_list()
    bus_mask = np.array([m == "BUS" for m in modes])
    rail_mask = ~bus_mask

    ax.scatter(lanes[bus_mask], otp[bus_mask], alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5, label="Bus", zorder=2)
    if np.any(rail_mask):
        ax.scatter(lanes[rail_mask], otp[rail_mask], alpha=0.7, s=50, color="#dc2626",
                   marker="D", edgecolors="white", linewidth=0.5, label="Rail", zorder=3)

    slope, intercept, r, p, _ = stats.linregress(lanes, otp)
    x_line = np.array([lanes.min(), lanes.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"fit: r={r:.3f}, p={p:.4f}")

    ax.set_xlabel("Length-weighted lane count")
    ax.set_ylabel("Average OTP")
    ax.set_title("Road Width (Lane Count) vs On-Time Performance")
    ax.legend(fontsize=9)
    save_chart(fig, OUT / "lanes_vs_otp_scatter.png")


def make_r2_progression(model_specs: list[tuple[str, dict]]) -> None:
    """Bar chart of adjusted R^2 across the nested models (same sample)."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(9, 6))

    labels = [label for label, _ in model_specs]
    adj_r2 = [m["adj_r_squared"] for _, m in model_specs]
    colors = ["#9ca3af", "#a78bfa", "#60a5fa", "#2563eb"][: len(labels)]

    bars = ax.bar(labels, adj_r2, color=colors, alpha=0.85)
    for bar, val in zip(bars, adj_r2):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.005, f"{val:.3f}",
                ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Adjusted R²")
    ax.set_title("Explained OTP Variance: Structural Baseline vs Road-Type Additions")
    ax.set_ylim(0, max(adj_r2) * 1.2)
    plt.xticks(rotation=15, ha="right")
    save_chart(fig, OUT / "r2_progression.png")


def make_coefficient_chart(base: dict, full: dict) -> None:
    """Compare standardized coefficients between base and full road-type models."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    base_feats = base["features"][1:]
    full_feats = full["features"][1:]
    base_betas = {f: b for f, b in zip(base_feats, base["beta_weights"][1:])}
    full_betas = {f: b for f, b in zip(full_feats, full["beta_weights"][1:])}
    full_pvals = {f: p for f, p in zip(full_feats, full["p_values"][1:])}

    y_pos = np.arange(len(full_feats))
    width = 0.35
    base_vals = [base_betas.get(f, 0.0) for f in full_feats]
    full_vals = [full_betas[f] for f in full_feats]

    ax.barh(y_pos + width / 2, base_vals, width, label="Structural baseline",
            color="#9ca3af", alpha=0.7)
    ax.barh(y_pos - width / 2, full_vals, width, label="+ road-type block",
            color="#2563eb", alpha=0.7)

    for i, f in enumerate(full_feats):
        p = full_pvals[f]
        marker = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        val = full_vals[i]
        ax.text(val + 0.01 if val >= 0 else val - 0.01, i - width / 2, marker,
                ha="left" if val >= 0 else "right", va="center", fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(full_feats)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Standardized Coefficient (Beta Weight)")
    ax.set_title(f"Model Comparison: Base R²={base['r_squared']:.3f} vs "
                 f"Full R²={full['r_squared']:.3f}")
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    save_chart(fig, OUT / "coefficient_comparison.png")


def make_partial_residual_chart(df: pl.DataFrame, base: dict) -> None:
    """Partial residual plot: base model residuals vs lane count."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    residuals = base["residuals"]
    lanes = df["weighted_lanes"].to_numpy()

    ax.scatter(lanes, residuals, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)
    slope, intercept, r, p, _ = stats.linregress(lanes, residuals)
    x_line = np.array([lanes.min(), lanes.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Length-weighted lane count")
    ax.set_ylabel("Base Model Residual (OTP)")
    ax.set_title("Partial Residual: Does Road Width Explain Remaining OTP Variance?")
    ax.legend(fontsize=9)
    save_chart(fig, OUT / "partial_residual.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@run_analysis(55, "Road Classification and OTP")
def main() -> None:
    """Entry point: load features, fit nested models, compare, chart, and save."""

    with phase("Loading and assembling features"):
        df_all = load_features()
        df = df_all.filter(pl.col("match_rate") >= MIN_MATCH_RATE)
        excluded = df_all.filter(pl.col("match_rate") < MIN_MATCH_RATE)
        n_rail = len(df.filter(pl.col("is_rail") == 1.0))
        n_bus = len(df.filter(pl.col("mode") == "BUS"))
        print(f"  {len(df)} routes after match_rate >= {MIN_MATCH_RATE} filter "
              f"({n_bus} BUS, {n_rail} RAIL)")
        if len(excluded) > 0:
            print(f"  Excluded ({len(excluded)}): "
                  + ", ".join(excluded.sort("match_rate")["route_id"].to_list()))
        print(f"\n  Lane count range: {df['weighted_lanes'].min():.2f} -- "
              f"{df['weighted_lanes'].max():.2f}")
        print(f"  Functional class range: {df['weighted_func_cls'].min():.2f} -- "
              f"{df['weighted_func_cls'].max():.2f}")
        print(f"  Speed range: {df['weighted_speed'].min():.0f} -- "
              f"{df['weighted_speed'].max():.0f} mph")
        print(f"  Median match rate: {df['match_rate'].median():.1%}")

    y = df["avg_otp"].to_numpy()
    base_features = ["stop_count", "span_km", "is_rail", "is_premium_bus",
                     "weekend_ratio", "n_munis"]

    # --- Model 1: structural baseline (Analysis 18 replication) ---
    X_base = np.column_stack([df[f].to_numpy().astype(float) for f in base_features])
    with phase("Fitting structural baseline (6 features)"):
        base = fit_ols(y, X_base, base_features)
        print_model(base, "Structural baseline (6 features)")

    # --- Model 2: + lane count alone ---
    lane_features = base_features + ["weighted_lanes"]
    X_lane = np.column_stack([df[f].to_numpy().astype(float) for f in lane_features])
    with phase("Fitting + lane count"):
        lane_model = fit_ols(y, X_lane, lane_features)
        print_model(lane_model, "Base + lane count")
        f_l, fp_l = f_test_nested(base, lane_model)
        print(f"\n  F-test for lane count: F = {f_l:.3f}, p = {fp_l:.4f}")
        print(f"  Adj R2: {base['adj_r_squared']:.4f} -> {lane_model['adj_r_squared']:.4f}")

    # --- Model 3: full road-type block ---
    full_features = base_features + ROAD_FEATURES
    X_full = np.column_stack([df[f].to_numpy().astype(float) for f in full_features])
    with phase("Fitting full road-type block (lanes + func_cls + speed)"):
        full = fit_ols(y, X_full, full_features)
        print_model(full, "Base + road-type block")
        f_f, fp_f = f_test_nested(base, full)
        print(f"\n  Joint F-test for road-type block: F = {f_f:.3f}, p = {fp_f:.4f}")
        print(f"  R2 change: {base['r_squared']:.4f} -> {full['r_squared']:.4f} "
              f"(+{full['r_squared'] - base['r_squared']:.4f})")
        print(f"  Adj R2 change: {base['adj_r_squared']:.4f} -> {full['adj_r_squared']:.4f} "
              f"(+{full['adj_r_squared'] - base['adj_r_squared']:.4f})")
        if fp_f < 0.05:
            print("  => Road type IS significant after controlling for structural features.")
        else:
            print("  => Road type is NOT significant after controlling for structural features.")

    # --- Model 4: truck_pct comparison (Analysis 27's best traffic predictor) ---
    truck_subset = df.filter(pl.col("avg_truck_pct").is_not_null())
    truck_model = None
    if len(truck_subset) >= 20:
        with phase(f"Fitting + truck_pct comparison (n={len(truck_subset)})"):
            y_t = truck_subset["avg_otp"].to_numpy()
            truck_features = base_features + ["avg_truck_pct"]
            X_t = np.column_stack([truck_subset[f].to_numpy().astype(float) for f in truck_features])
            truck_model = fit_ols(y_t, X_t, truck_features)
            print_model(truck_model, "Base + truck_pct (for comparison)")

    # --- VIF for full model ---
    with phase("VIF (full road-type model)"):
        vifs = compute_vif(X_full, full_features)
        for feat, vif in vifs.items():
            flag = " ** HIGH" if vif > 5 else ""
            print(f"  {feat:<20s} VIF = {vif:.2f}{flag}")

    # --- Descriptive correlations ---
    with phase("Descriptive correlations with OTP"):
        for feat in ROAD_FEATURES + ["arterial_share", "divided_share"]:
            sub = df.drop_nulls(subset=[feat])
            corr = correlate(sub, feat, "avg_otp")
            sig = "*" if corr["pearson_p"] < 0.05 else ""
            print(f"  {feat:<20s} r = {corr['pearson_r']:+.3f}, "
                  f"p = {corr['pearson_p']:.4f} (n={len(sub)}) {sig}")
        print("\n  Road-type collinearity with structural features:")
        for feat in ["stop_count", "span_km"]:
            corr = correlate(df, "weighted_lanes", feat)
            print(f"  weighted_lanes vs {feat:<14s}: r = {corr['pearson_r']:+.3f}, "
                  f"p = {corr['pearson_p']:.4f}")

    # --- Bus-only subgroup ---
    bus_df = df.filter(pl.col("mode") == "BUS")
    with phase(f"Fitting bus-only models ({len(bus_df)} routes)"):
        y_bus = bus_df["avg_otp"].to_numpy()
        bus_base_feats = ["stop_count", "span_km", "is_premium_bus", "weekend_ratio", "n_munis"]
        bus_full_feats = bus_base_feats + ROAD_FEATURES
        X_bus_base = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_base_feats])
        X_bus_full = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_full_feats])
        bus_base = fit_ols(y_bus, X_bus_base, bus_base_feats)
        bus_full = fit_ols(y_bus, X_bus_full, bus_full_feats)
        f_b, fp_b = f_test_nested(bus_base, bus_full)
        print(f"  Bus-only joint F-test for road-type block: F = {f_b:.3f}, p = {fp_b:.4f}")
        print(f"  Adj R2: {bus_base['adj_r_squared']:.4f} -> {bus_full['adj_r_squared']:.4f}")

    with phase("Saving CSVs"):
        rows = []
        models = [
            (base, "base_6feat"),
            (lane_model, "base_plus_lanes"),
            (full, "base_plus_roadblock"),
            (bus_base, "bus_base"),
            (bus_full, "bus_plus_roadblock"),
        ]
        if truck_model is not None:
            models.append((truck_model, "base_plus_truck"))
        for model, label in models:
            for i, feat in enumerate(model["features"]):
                bw = model["beta_weights"][i]
                rows.append({
                    "model": label,
                    "feature": feat,
                    "coefficient": model["coefficients"][i],
                    "std_error": model["std_errors"][i],
                    "p_value": model["p_values"][i],
                    "beta_weight": bw if bw is not None else float("nan"),
                    "r_squared": model["r_squared"],
                    "adj_r_squared": model["adj_r_squared"],
                    "n": model["n"],
                })
        save_csv(pl.DataFrame(rows), OUT / "model_comparison.csv")

        vif_df = pl.DataFrame([{"feature": f, "vif": v} for f, v in vifs.items()])
        save_csv(vif_df, OUT / "vif_table.csv")

        summary_df = df.select([
            "route_id", "route_name", "mode", "avg_otp",
            "weighted_lanes", "weighted_func_cls", "weighted_speed",
            "arterial_share", "divided_share", "avg_truck_pct",
            "match_rate", "n_segments", "stop_count", "span_km",
        ]).sort("weighted_lanes", descending=True)
        save_csv(summary_df, OUT / "route_road_class_summary.csv")

    with phase("Generating charts"):
        make_lanes_scatter(df)
        progression = [
            ("Baseline\n(structural)", base),
            ("+ lane count", lane_model),
            ("+ road block\n(lanes+func+speed)", full),
        ]
        if truck_model is None:
            make_r2_progression(progression)
        else:
            # truck_model uses the same sample only if no nulls dropped; guard on n.
            specs = list(progression)
            if truck_model["n"] == base["n"]:
                specs.insert(1, ("+ truck %\n(Analysis 27)", truck_model))
            make_r2_progression(specs)
        make_coefficient_chart(base, full)
        make_partial_residual_chart(df, base)


if __name__ == "__main__":
    main()
