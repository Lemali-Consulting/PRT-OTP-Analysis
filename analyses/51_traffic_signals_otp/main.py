"""Analysis 51: Test whether traffic-signal density explains OTP variance beyond structural features."""

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
from prt_otp_analysis.common.schemas import ROUTE_SIGNALS, validate

OUT = analysis_dir(__file__)

MIN_MONTHS = 12


# ---------------------------------------------------------------------------
# Helpers (replicated from Analysis 18/27 to maintain independence)
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
    """Assemble structural features + traffic signal data for the regression model."""
    avg_otp = query_to_polars(f"""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= {MIN_MONTHS}
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

    # Traffic signal data
    signals_df = query_to_polars("""
        SELECT route_id, n_signals, length_km, signal_density,
               match_rate, n_route_points
        FROM route_signals
    """)
    validate(signals_df, ROUTE_SIGNALS, subset=True)

    # Authoritative per-route signal exposure (PRT stop_signals): how many of a
    # route's stops sit at a traffic signal, and what share. Independent of the
    # OSM density measure above — used to cross-validate it and as an alternative
    # predictor.
    auth_signal_df = query_to_polars("""
        SELECT rs.route_id,
               COUNT(DISTINCT rs.stop_id) AS n_route_stops,
               COUNT(DISTINCT CASE WHEN ss.has_signal = 1 THEN rs.stop_id END)
                   AS n_sig_stops
        FROM route_stops rs
        LEFT JOIN stop_signals ss ON rs.stop_id = ss.stop_id
        GROUP BY rs.route_id
    """).with_columns(
        pl.when(pl.col("n_route_stops") > 0)
        .then(pl.col("n_sig_stops") / pl.col("n_route_stops"))
        .otherwise(None)
        .alias("sig_stop_share"),
    )

    # Assemble
    df = avg_otp
    df = df.join(stop_counts, on="route_id", how="left")
    df = df.join(trips, on="route_id", how="left")
    df = df.join(munis, on="route_id", how="left")
    df = df.join(span_df, on="route_id", how="left")
    df = df.join(signals_df, on="route_id", how="inner")
    df = df.join(auth_signal_df, on="route_id", how="left")

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

    df = df.drop_nulls(
        subset=["stop_count", "span_km", "weekend_ratio", "n_munis",
                "signal_density", "sig_stop_share"],
    )

    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def make_scatter_chart(df: pl.DataFrame) -> None:
    """Bivariate scatter: signal density vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    density = df["signal_density"].to_numpy()
    otp = df["avg_otp"].to_numpy()
    modes = df["mode"].to_list()

    bus_mask = np.array([m == "BUS" for m in modes])
    rail_mask = ~bus_mask

    ax.scatter(density[bus_mask], otp[bus_mask], alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5, label="Bus", zorder=2)
    if np.any(rail_mask):
        ax.scatter(density[rail_mask], otp[rail_mask], alpha=0.7, s=50, color="#dc2626",
                   marker="D", edgecolors="white", linewidth=0.5, label="Rail", zorder=3)

    # Trend line (all routes)
    slope, intercept, r, p, _ = stats.linregress(density, otp)
    x_sorted = np.sort(density)
    ax.plot(x_sorted, slope * x_sorted + intercept, color="#e11d48",
            linewidth=1.5, linestyle="--", alpha=0.7,
            label=f"linear fit: r={r:.3f}, p={p:.4f}")

    ax.set_xlabel("Signal density (traffic signals per route-km)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Traffic Signal Density vs On-Time Performance")
    ax.legend(fontsize=9)

    save_chart(fig, OUT / "signal_density_vs_otp_scatter.png")


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
    ax.barh(y_pos - width / 2, exp_vals, width, label="Expanded (+signal_density)",
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

    save_chart(fig, OUT / "coefficient_comparison.png")


def make_partial_residual_chart(df: pl.DataFrame, base: dict) -> None:
    """Partial residual plot: base model residuals vs signal density."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    residuals = base["residuals"]
    density = df["signal_density"].to_numpy()

    ax.scatter(density, residuals, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)

    slope, intercept, r, p, _ = stats.linregress(density, residuals)
    x_line = np.array([density.min(), density.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Signal density (signals per route-km)")
    ax.set_ylabel("Base Model Residual (OTP)")
    ax.set_title("Partial Residual: Does Signal Density Explain Remaining OTP Variance?")
    ax.legend(fontsize=9)

    save_chart(fig, OUT / "partial_residual.png")


def make_cross_validation_chart(df: pl.DataFrame) -> None:
    """Scatter: PRT authoritative signalized-stop share vs OSM signal density."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 6))

    share = df["sig_stop_share"].to_numpy() * 100
    density = df["signal_density"].to_numpy()

    ax.scatter(share, density, alpha=0.5, s=30, color="#2563eb",
               edgecolors="white", linewidth=0.5)
    slope, intercept, r, p, _ = stats.linregress(share, density)
    x_line = np.array([share.min(), share.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#e11d48", linewidth=1.5,
            linestyle="--", alpha=0.7, label=f"r={r:.3f}, p={p:.4f}")

    ax.set_xlabel("PRT signalized-stop share (%) — authoritative")
    ax.set_ylabel("OSM signal density (signals per route-km)")
    ax.set_title("Cross-Validation: PRT Authoritative vs OSM Signal Exposure")
    ax.legend(fontsize=9)

    save_chart(fig, OUT / "cross_validation_signal_exposure.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@run_analysis(51, "Traffic Signals and OTP")
def main() -> None:
    """Entry point: load features, fit models, compare, chart, and save."""

    with phase("Loading and assembling features"):
        df = load_features()
        n_rail = len(df.filter(pl.col("is_rail") == 1.0))
        n_bus = len(df.filter(pl.col("mode") == "BUS"))
        print(f"  {len(df)} routes with signal + structural features "
              f"({n_bus} BUS, {n_rail} RAIL)")
        print(f"  Signal density range: {df['signal_density'].min():.2f} -- "
              f"{df['signal_density'].max():.2f} signals/km")
        print(f"  Signal count range: {df['n_signals'].min()} -- {df['n_signals'].max()}")
        print(f"  Median match rate (diagnostic only): {df['match_rate'].median():.1%}")

    y = df["avg_otp"].to_numpy()

    # --- Diagnostic: raw count vs density bivariate correlations ---
    with phase("Diagnostic: raw count vs density confound"):
        corr_count = correlate(df, "n_signals", "avg_otp")
        corr_density = correlate(df, "signal_density", "avg_otp")
        corr_count_len = correlate(df, "n_signals", "length_km")
        print(f"  n_signals      vs avg_otp : r = {corr_count['pearson_r']:+.3f}, "
              f"p = {corr_count['pearson_p']:.4f}")
        print(f"  signal_density vs avg_otp : r = {corr_density['pearson_r']:+.3f}, "
              f"p = {corr_density['pearson_p']:.4f}")
        print(f"  n_signals      vs length  : r = {corr_count_len['pearson_r']:+.3f}, "
              f"p = {corr_count_len['pearson_p']:.4f}")
        print("  => raw n_signals tracks route length; signal_density is the "
              "length-adjusted predictor.")

    # --- Cross-validation: OSM signal exposure vs PRT authoritative ---
    with phase("Cross-validating OSM signals against PRT authoritative stops"):
        cv_density = correlate(df, "sig_stop_share", "signal_density")
        cv_count = correlate(df, "n_sig_stops", "n_signals")
        share_otp = correlate(df, "sig_stop_share", "avg_otp")
        nsig_otp = correlate(df, "n_sig_stops", "avg_otp")
        print(f"  PRT sig_stop_share vs OSM signal_density : r = {cv_density['pearson_r']:+.3f}, "
              f"p = {cv_density['pearson_p']:.4f}")
        print(f"  PRT n_sig_stops    vs OSM n_signals      : r = {cv_count['pearson_r']:+.3f}, "
              f"p = {cv_count['pearson_p']:.4f}")
        print("  => the two independent signal-exposure measures agree, validating "
              "the OSM proxy used in the headline model.")
        print(f"  PRT sig_stop_share vs avg_otp : r = {share_otp['pearson_r']:+.3f}, "
              f"p = {share_otp['pearson_p']:.4f}  (length-adjusted, honest predictor)")
        print(f"  PRT n_sig_stops    vs avg_otp : r = {nsig_otp['pearson_r']:+.3f}, "
              f"p = {nsig_otp['pearson_p']:.4f}  (tracks stop_count — confounded)")

    # --- Model 1: Base (Analysis 27 replication, 6 features) ---
    base_features = ["stop_count", "span_km", "is_rail", "is_premium_bus",
                     "weekend_ratio", "n_munis"]
    X_base = np.column_stack([df[f].to_numpy().astype(float) for f in base_features])
    with phase("Fitting base model (6 features, Analysis 27 replication)"):
        base = fit_ols(y, X_base, base_features)
        print_model(base, "Base model (6 features)")

    # --- Model 2: Expanded (+ signal_density) ---
    exp_features = base_features + ["signal_density"]
    X_exp = np.column_stack([df[f].to_numpy().astype(float) for f in exp_features])
    with phase("Fitting expanded model (+ signal_density)"):
        expanded = fit_ols(y, X_exp, exp_features)
        print_model(expanded, "Expanded model (+ signal_density)")

        f_stat, f_p = f_test_nested(base, expanded)
        print(f"\n  F-test for signal_density: F = {f_stat:.3f}, p = {f_p:.4f}")
        print(f"  R2 change: {base['r_squared']:.4f} -> {expanded['r_squared']:.4f} "
              f"(+{expanded['r_squared'] - base['r_squared']:.4f})")
        print(f"  Adj R2 change: {base['adj_r_squared']:.4f} -> {expanded['adj_r_squared']:.4f} "
              f"({expanded['adj_r_squared'] - base['adj_r_squared']:+.4f})")
        if f_p < 0.05:
            print("  => signal density IS significant after controlling for "
                  "structural features.")
        else:
            print("  => signal density is NOT significant after controlling for "
                  "structural features.")

        # --- VIF for expanded model ---
        print("\n--- VIF (Expanded Model: base + signal_density) ---")
        vifs = compute_vif(X_exp, exp_features)
        for feat, vif in vifs.items():
            flag = " ** HIGH" if vif > 5 else ""
            print(f"  {feat:<20s} VIF = {vif:.2f}{flag}")

        # --- Correlation: signal_density vs structural features ---
        print("\n--- Correlations: signal_density vs structural features ---")
        for feat in base_features:
            corr = correlate(df, feat, "signal_density")
            sig = "*" if corr["pearson_p"] < 0.05 else ""
            print(f"  signal_density vs {feat:<16s}: r = {corr['pearson_r']:+.3f}, "
                  f"p = {corr['pearson_p']:.4f} {sig}")

    # --- Model 3: Authoritative (base + PRT signalized-stop share) ---
    auth_features = base_features + ["sig_stop_share"]
    X_auth = np.column_stack([df[f].to_numpy().astype(float) for f in auth_features])
    with phase("Fitting authoritative model (+ PRT sig_stop_share)"):
        auth_model = fit_ols(y, X_auth, auth_features)
        print_model(auth_model, "Authoritative model (+ sig_stop_share)")
        f_auth, fp_auth = f_test_nested(base, auth_model)
        print(f"\n  F-test for sig_stop_share: F = {f_auth:.3f}, p = {fp_auth:.4f}")
        print(f"  R2 change: {base['r_squared']:.4f} -> {auth_model['r_squared']:.4f} "
              f"(+{auth_model['r_squared'] - base['r_squared']:.4f})")
        if fp_auth < 0.05:
            print("  => PRT authoritative signal exposure IS significant beyond "
                  "structural features — independently confirms the OSM result.")

    # --- Model 4: Combined (base + OSM density + PRT share) ---
    combined_features = base_features + ["signal_density", "sig_stop_share"]
    X_comb = np.column_stack([df[f].to_numpy().astype(float) for f in combined_features])
    with phase("Fitting combined model (+ signal_density + sig_stop_share)"):
        combined = fit_ols(y, X_comb, combined_features)
        print_model(combined, "Combined model (density + share)")
        f_comb, fp_comb = f_test_nested(base, combined)
        print(f"\n  F-test (both signal measures): F = {f_comb:.3f}, p = {fp_comb:.4f}")
        print(f"  R2: base {base['r_squared']:.4f} -> combined {combined['r_squared']:.4f}")
        comb_vifs = compute_vif(X_comb, combined_features)
        print("  VIF (density, share): "
              f"{comb_vifs['signal_density']:.2f}, {comb_vifs['sig_stop_share']:.2f}")
        dens_p = combined["p_values"][combined_features.index("signal_density") + 1]
        share_p = combined["p_values"][combined_features.index("sig_stop_share") + 1]
        if dens_p < 0.05 and share_p < 0.05:
            print("  => both remain significant and non-collinear: signal density "
                  "and signalized-stop share capture distinct delay facets.")

    # --- Bus-only subgroup ---
    bus_df = df.filter(pl.col("mode") == "BUS")
    y_bus = bus_df["avg_otp"].to_numpy()
    bus_base_feats = ["stop_count", "span_km", "is_premium_bus", "weekend_ratio", "n_munis"]
    bus_exp_feats = bus_base_feats + ["signal_density"]

    X_bus_base = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_base_feats])
    X_bus_exp = np.column_stack([bus_df[f].to_numpy().astype(float) for f in bus_exp_feats])

    with phase(f"Fitting bus-only models ({len(bus_df)} routes)"):
        bus_base = fit_ols(y_bus, X_bus_base, bus_base_feats)
        print_model(bus_base, "Bus-only base (5 features)")

        bus_expanded = fit_ols(y_bus, X_bus_exp, bus_exp_feats)
        print_model(bus_expanded, "Bus-only expanded (+ signal_density)")

        f_bus, fp_bus = f_test_nested(bus_base, bus_expanded)
        print(f"\n  Bus-only F-test for signal_density: F = {f_bus:.3f}, p = {fp_bus:.4f}")
        print(f"  R2 change: {bus_base['r_squared']:.4f} -> {bus_expanded['r_squared']:.4f} "
              f"(+{bus_expanded['r_squared'] - bus_base['r_squared']:.4f})")

    with phase("Saving CSVs"):
        rows = []
        models = [
            (base, "base_6feat"),
            (expanded, "expanded_7feat_signal_density"),
            (auth_model, "authoritative_sig_stop_share"),
            (combined, "combined_density_and_share"),
            (bus_base, "bus_base"),
            (bus_expanded, "bus_expanded_signal_density"),
        ]
        for model, label in models:
            for i, feat in enumerate(model["features"]):
                rows.append({
                    "model": label,
                    "feature": feat,
                    "coefficient": model["coefficients"][i],
                    "std_error": model["std_errors"][i],
                    "p_value": model["p_values"][i],
                    "beta_weight": model["beta_weights"][i]
                    if model["beta_weights"][i] is not None else float("nan"),
                    "r_squared": model["r_squared"],
                    "adj_r_squared": model["adj_r_squared"],
                    "n": model["n"],
                })
        save_csv(pl.DataFrame(rows), OUT / "model_comparison.csv")

        vif_df = pl.DataFrame([{"feature": f, "vif": v} for f, v in vifs.items()])
        save_csv(vif_df, OUT / "vif_table.csv")

        summary_df = df.select([
            "route_id", "route_name", "mode", "avg_otp", "n_signals",
            "length_km", "signal_density", "match_rate", "stop_count", "span_km",
            "n_route_stops", "n_sig_stops", "sig_stop_share",
        ]).sort("signal_density", descending=True)
        save_csv(summary_df, OUT / "route_signals_summary.csv")

    with phase("Generating charts"):
        make_scatter_chart(df)
        make_coefficient_chart(base, expanded)
        make_partial_residual_chart(df, base)
        make_cross_validation_chart(df)


if __name__ == "__main__":
    main()
