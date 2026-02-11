"""Multivariate OLS model combining structural predictors of OTP."""

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


def load_features() -> pl.DataFrame:
    """Assemble all features for the regression model."""
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
        FROM route_stops
        GROUP BY route_id
    """)
    trips = query_to_polars("""
        SELECT route_id,
               MAX(trips_wd) AS max_wd,
               MAX(trips_sa) AS max_sa,
               MAX(trips_su) AS max_su
        FROM route_stops
        GROUP BY route_id
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

    df = avg_otp
    df = df.join(stop_counts, on="route_id", how="left")
    df = df.join(trips, on="route_id", how="left")
    df = df.join(munis, on="route_id", how="left")
    df = df.join(span_df, on="route_id", how="left")

    df = df.with_columns(
        pl.when(pl.col("max_wd") > 0)
        .then((pl.col("max_sa") + pl.col("max_su")) / (2.0 * pl.col("max_wd")))
        .otherwise(0.0)
        .alias("weekend_ratio")
    )
    df = df.with_columns(
        pl.when(pl.col("mode") == "RAIL").then(1.0).otherwise(0.0).alias("is_rail")
    )
    df = df.with_columns(
        pl.when(pl.col("mode") == "BUS")
        .then(pl.col("route_id").map_elements(classify_bus_route, return_dtype=pl.Utf8))
        .otherwise(pl.lit("non_bus"))
        .alias("bus_subtype")
    )
    df = df.with_columns(
        pl.when(pl.col("bus_subtype").is_in(["busway", "flyer", "express", "limited"]))
        .then(1.0)
        .otherwise(0.0)
        .alias("is_premium_bus")
    )
    df = df.drop_nulls(subset=["stop_count", "span_km", "weekend_ratio", "n_munis"])

    return df


def compute_vif(X_raw: np.ndarray, feature_names: list[str]) -> dict[str, float]:
    """Compute Variance Inflation Factor for each predictor."""
    n, k = X_raw.shape
    vifs = {}
    for j in range(k):
        y_j = X_raw[:, j]
        X_other = np.delete(X_raw, j, axis=1)
        X_other = np.column_stack([np.ones(n), X_other])
        beta, residuals, _, _ = np.linalg.lstsq(X_other, y_j, rcond=None)
        y_hat = X_other @ beta
        ss_res = np.sum((y_j - y_hat) ** 2)
        ss_tot = np.sum((y_j - np.mean(y_j)) ** 2)
        r2_j = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        vifs[feature_names[j]] = 1.0 / (1.0 - r2_j) if r2_j < 1.0 else float("inf")
    return vifs


def fit_ols(y: np.ndarray, X_raw: np.ndarray, feature_names: list[str]) -> tuple[dict, np.ndarray]:
    """Fit OLS regression using lstsq for numerical stability."""
    n, k = X_raw.shape
    X = np.column_stack([np.ones(n), X_raw])

    # OLS via least squares (more stable than matrix inversion)
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ beta
    residuals = y - y_hat

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
    mse = ss_res / (n - k - 1)

    # Standard errors via (X'X)^-1 * MSE (using pseudoinverse for stability)
    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(XtX_inv) * mse)
    t_vals = beta / se
    p_vals = [2 * (1 - stats.t.cdf(abs(t), df=n - k - 1)) for t in t_vals]

    # Standardized beta weights (using sample std, ddof=1)
    x_stds = np.std(X_raw, axis=0, ddof=1)
    y_std = np.std(y, ddof=1)
    beta_weights = beta[1:] * x_stds / y_std

    results = {
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "k": k,
        "features": ["intercept"] + feature_names,
        "coefficients": beta.tolist(),
        "std_errors": se.tolist(),
        "t_values": t_vals.tolist(),
        "p_values": p_vals,
        "beta_weights": [None] + beta_weights.tolist(),
    }
    return results, y_hat


def print_model(results: dict, label: str) -> None:
    """Print formatted model results."""
    print(f"\n  {label}:")
    print(f"  R² = {results['r_squared']:.4f}, Adj R² = {results['adj_r_squared']:.4f}, "
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


def make_charts(df: pl.DataFrame, results: dict, y_hat: np.ndarray) -> None:
    """Generate coefficient plot and predicted vs actual scatter."""
    plt = setup_plotting()

    # Coefficient plot (standardized)
    fig, ax = plt.subplots(figsize=(10, 6))
    features = results["features"][1:]
    betas = [b for b in results["beta_weights"][1:]]
    p_vals = results["p_values"][1:]
    colors = ["#22c55e" if p < 0.05 else "#9ca3af" for p in p_vals]

    y_pos = range(len(features))
    ax.barh(y_pos, betas, color=colors, edgecolor="white")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(features)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Standardized Coefficient (Beta Weight)")
    ax.set_title(f"Multivariate OTP Model: Feature Importance\n"
                 f"R²={results['r_squared']:.3f}, Adj R²={results['adj_r_squared']:.3f}, n={results['n']}")

    for i, (b, p) in enumerate(zip(betas, p_vals)):
        marker = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        ax.text(b + 0.01 if b >= 0 else b - 0.01, i, marker,
                ha="left" if b >= 0 else "right", va="center", fontsize=10)

    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT / "coefficient_plot.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'coefficient_plot.png'}")

    # Predicted vs actual
    fig, ax = plt.subplots(figsize=(8, 8))
    y_actual = df["avg_otp"].to_list()
    ax.scatter(y_hat, y_actual, s=30, alpha=0.6, color="#3b82f6", edgecolors="white", linewidths=0.5)
    lims = [min(min(y_hat), min(y_actual)) - 0.02, max(max(y_hat), max(y_actual)) + 0.02]
    ax.plot(lims, lims, "--", color="#dc2626", linewidth=1, label="Perfect prediction")
    ax.set_xlabel("Predicted OTP")
    ax.set_ylabel("Actual OTP")
    ax.set_title(f"Predicted vs Actual OTP (R²={results['r_squared']:.3f})")
    ax.legend()
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(OUT / "predicted_vs_actual.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'predicted_vs_actual.png'}")


def main() -> None:
    """Entry point: load features, fit models, report, and visualize."""
    print("=" * 60)
    print("Analysis 18: Multivariate OTP Model")
    print("=" * 60)

    print("\nLoading and assembling features...")
    df = load_features()
    n_rail = len(df.filter(pl.col("is_rail") == 1.0))
    n_bus = len(df.filter(pl.col("mode") == "BUS"))
    print(f"  {len(df)} routes with complete feature set ({n_bus} BUS, {n_rail} RAIL)")

    # --- Full model (all 6 features) ---
    full_features = ["stop_count", "span_km", "is_rail", "is_premium_bus",
                     "weekend_ratio", "n_munis"]
    y = np.array(df["avg_otp"].to_list())
    X_full = np.column_stack([np.array(df[f].to_list(), dtype=float) for f in full_features])

    print("\n--- VIF (Variance Inflation Factors) ---")
    vifs = compute_vif(X_full, full_features)
    for feat, vif in vifs.items():
        flag = " ** HIGH" if vif > 5 else ""
        print(f"  {feat:<20s} VIF = {vif:.2f}{flag}")

    print("\nFitting full model (6 features)...")
    full_results, y_hat_full = fit_ols(y, X_full, full_features)
    print_model(full_results, "Full model")

    # --- Reduced model (without n_munis suppressor) ---
    reduced_features = ["stop_count", "span_km", "is_rail", "is_premium_bus", "weekend_ratio"]
    X_reduced = np.column_stack([np.array(df[f].to_list(), dtype=float) for f in reduced_features])
    print("\nFitting reduced model (without n_munis)...")
    reduced_results, _ = fit_ols(y, X_reduced, reduced_features)
    print_model(reduced_results, "Reduced model (no n_munis)")

    # --- Bus-only model ---
    bus_df = df.filter(pl.col("mode") == "BUS")
    bus_features = ["stop_count", "span_km", "is_premium_bus", "weekend_ratio", "n_munis"]
    y_bus = np.array(bus_df["avg_otp"].to_list())
    X_bus = np.column_stack([np.array(bus_df[f].to_list(), dtype=float) for f in bus_features])
    print(f"\nFitting bus-only model ({len(bus_df)} routes)...")
    bus_results, _ = fit_ols(y_bus, X_bus, bus_features)
    print_model(bus_results, "Bus-only model")

    # Save full model coefficients
    coeff_df = pl.DataFrame({
        "feature": full_results["features"],
        "coefficient": full_results["coefficients"],
        "std_error": full_results["std_errors"],
        "t_value": full_results["t_values"],
        "p_value": full_results["p_values"],
        "beta_weight": [b if b is not None else float("nan") for b in full_results["beta_weights"]],
    })
    coeff_df.write_csv(OUT / "model_coefficients.csv")
    print(f"\n  Saved to {OUT / 'model_coefficients.csv'}")

    print("\nGenerating charts...")
    make_charts(df, full_results, y_hat_full)

    print("\nDone.")


if __name__ == "__main__":
    main()
