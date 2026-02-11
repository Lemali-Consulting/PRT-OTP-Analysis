"""Cluster routes by detrended OTP time-series correlation to find co-moving groups."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 36
MIN_OVERLAP = 24


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load OTP time series and route metadata."""
    otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode, o.month, o.otp
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
    """)
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops
        GROUP BY route_id
    """)
    return otp, stop_counts


def detrend(otp: pl.DataFrame) -> pl.DataFrame:
    """Subtract the system-wide monthly mean OTP from each route's OTP."""
    monthly_mean = (
        otp.group_by("month")
        .agg(pl.col("otp").mean().alias("system_otp"))
    )
    otp = otp.join(monthly_mean, on="month", how="left")
    otp = otp.with_columns(
        (pl.col("otp") - pl.col("system_otp")).alias("otp_detrended")
    )
    return otp


def build_correlation_matrix(otp: pl.DataFrame) -> tuple[np.ndarray, list[str], list[str], int]:
    """Build a pairwise Pearson correlation matrix on detrended OTP."""
    # Filter to routes with sufficient months
    route_months = otp.group_by("route_id").len().filter(pl.col("len") >= MIN_MONTHS)
    valid_routes = sorted(route_months["route_id"].to_list())

    otp_filtered = otp.filter(pl.col("route_id").is_in(valid_routes))

    # Pivot on detrended values
    pivot = otp_filtered.pivot(on="month", index="route_id", values="otp_detrended")
    route_ids = pivot["route_id"].to_list()

    month_cols = [c for c in pivot.columns if c != "route_id"]
    matrix = pivot.select(month_cols).to_numpy()

    n = len(route_ids)
    corr = np.full((n, n), np.nan)
    n_excluded = 0

    for i in range(n):
        for j in range(i, n):
            mask = ~np.isnan(matrix[i]) & ~np.isnan(matrix[j])
            if mask.sum() >= MIN_OVERLAP:
                r = np.corrcoef(matrix[i][mask], matrix[j][mask])[0, 1]
                corr[i, j] = r
                corr[j, i] = r
            else:
                # Leave as NaN instead of imputing 0.0
                n_excluded += 1
        corr[i, i] = 1.0

    # For clustering, replace remaining NaN pairs with median correlation
    median_corr = np.nanmedian(corr[np.triu_indices(n, k=1)])
    nan_mask = np.isnan(corr)
    corr[nan_mask] = median_corr

    return corr, route_ids, month_cols, n_excluded


def silhouette_score(dist_matrix: np.ndarray, labels: np.ndarray) -> float:
    """Compute mean silhouette score from a precomputed distance matrix."""
    n = len(labels)
    scores = np.zeros(n)
    for i in range(n):
        own_cluster = labels[i]
        own_mask = labels == own_cluster
        if own_mask.sum() <= 1:
            scores[i] = 0.0
            continue
        a_i = dist_matrix[i, own_mask].sum() / (own_mask.sum() - 1)
        b_i = np.inf
        for c in np.unique(labels):
            if c == own_cluster:
                continue
            other_mask = labels == c
            b_c = dist_matrix[i, other_mask].mean()
            b_i = min(b_i, b_c)
        scores[i] = (b_i - a_i) / max(a_i, b_i) if max(a_i, b_i) > 0 else 0.0
    return scores.mean()


def cluster_routes(corr: np.ndarray) -> tuple[np.ndarray, np.ndarray, int, dict]:
    """Cluster with average linkage; pick k by silhouette score."""
    dist = np.clip(1 - corr, 0, 2)
    np.fill_diagonal(dist, 0)
    condensed = squareform(dist)
    linkage_matrix = linkage(condensed, method="average")

    # Find best k via silhouette score
    sil_scores = {}
    for k in range(3, 11):
        labels_k = fcluster(linkage_matrix, t=k, criterion="maxclust")
        sil_scores[k] = silhouette_score(dist, labels_k)

    best_k = max(sil_scores, key=sil_scores.get)
    labels = fcluster(linkage_matrix, t=best_k, criterion="maxclust")

    return labels, linkage_matrix, best_k, sil_scores


def make_dendrogram(linkage_matrix: np.ndarray, route_ids: list[str],
                    route_meta: pl.DataFrame) -> None:
    """Generate a dendrogram of route clusters."""
    plt = setup_plotting()

    labels = []
    for rid in route_ids:
        row = route_meta.filter(pl.col("route_id") == rid)
        if len(row) > 0:
            labels.append(f"{rid}")
        else:
            labels.append(rid)

    fig, ax = plt.subplots(figsize=(16, 8))
    dendrogram(linkage_matrix, labels=labels, leaf_rotation=90, leaf_font_size=7, ax=ax)
    ax.set_title("Route OTP Clustering (Average Linkage on Detrended Correlation Distance)")
    ax.set_ylabel("Distance (1 - r)")
    fig.tight_layout()
    fig.savefig(OUT / "dendrogram.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'dendrogram.png'}")


def make_heatmap(corr: np.ndarray, route_ids: list[str], labels: np.ndarray) -> None:
    """Generate a correlation heatmap ordered by cluster assignment."""
    plt = setup_plotting()

    order = np.argsort(labels)
    corr_sorted = corr[np.ix_(order, order)]
    sorted_ids = [route_ids[i] for i in order]

    fig, ax = plt.subplots(figsize=(14, 12))
    im = ax.imshow(corr_sorted, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_title("Pairwise Detrended OTP Correlation (Ordered by Cluster)")

    tick_positions = list(range(0, len(sorted_ids), 5))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([sorted_ids[i] for i in tick_positions], rotation=90, fontsize=6)
    ax.set_yticks(tick_positions)
    ax.set_yticklabels([sorted_ids[i] for i in tick_positions], fontsize=6)

    fig.colorbar(im, ax=ax, label="Pearson r (detrended)", shrink=0.8)
    fig.tight_layout()
    fig.savefig(OUT / "correlation_heatmap.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'correlation_heatmap.png'}")


def main() -> None:
    """Entry point: load, detrend, correlate, cluster, and visualize."""
    print("=" * 60)
    print("Analysis 13: Cross-Route Correlation Clustering")
    print("=" * 60)

    print("\nLoading data...")
    otp, stop_counts = load_data()

    print("\nDetrending (subtracting system-wide monthly mean)...")
    otp = detrend(otp)

    print("\nBuilding detrended correlation matrix...")
    corr, route_ids, month_cols, n_excluded = build_correlation_matrix(otp)
    print(f"  {len(route_ids)} routes with {MIN_MONTHS}+ months of data")
    print(f"  Correlation matrix: {corr.shape}")
    print(f"  {n_excluded} route pairs excluded for <{MIN_OVERLAP} overlapping months (imputed with median)")

    print("\nClustering routes (silhouette-optimized k)...")
    labels, linkage_matrix, best_k, sil_scores = cluster_routes(corr)
    print(f"  Silhouette scores by k:")
    for k, s in sorted(sil_scores.items()):
        marker = " <-- best" if k == best_k else ""
        print(f"    k={k}: {s:.4f}{marker}")
    print(f"  Selected k={best_k}")

    # Build metadata for output
    route_meta = query_to_polars("""
        SELECT r.route_id, r.route_name, r.mode
        FROM routes r
    """)
    avg_otp = otp.group_by("route_id").agg(pl.col("otp").mean().alias("avg_otp"))

    membership = pl.DataFrame({
        "route_id": route_ids,
        "cluster": labels.tolist(),
    })
    membership = membership.join(route_meta, on="route_id", how="left")
    membership = membership.join(avg_otp, on="route_id", how="left")
    membership = membership.join(stop_counts, on="route_id", how="left")
    membership = membership.sort(["cluster", "route_id"])

    print("\nCluster summary:")
    for c in sorted(membership["cluster"].unique().to_list()):
        cluster = membership.filter(pl.col("cluster") == c)
        n = len(cluster)
        avg = cluster["avg_otp"].mean()
        modes = cluster["mode"].value_counts().sort("count", descending=True)
        top_mode = modes["mode"][0] if len(modes) > 0 else "?"
        avg_stops = cluster["stop_count"].mean()
        print(f"  Cluster {c}: {n} routes, avg OTP={avg:.1%}, "
              f"primary mode={top_mode}, avg stops={avg_stops:.0f}")

    print("\nSaving CSV...")
    membership.write_csv(OUT / "cluster_membership.csv")
    print(f"  Saved to {OUT / 'cluster_membership.csv'}")

    print("\nGenerating charts...")
    make_dendrogram(linkage_matrix, route_ids, route_meta)
    make_heatmap(corr, route_ids, labels)

    print("\nDone.")


if __name__ == "__main__":
    main()
