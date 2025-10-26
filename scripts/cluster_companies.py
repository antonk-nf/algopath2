#!/usr/bin/env python3
"""Cluster companies from correlation export using hierarchical clustering."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


def _load_correlations(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Correlation file not found: {csv_path}")

    df = pd.read_csv(
        csv_path,
        comment="#",
        header=None,
        names=["company1", "company2", "correlation"],
        dtype={"company1": str, "company2": str, "correlation": float},
    )

    if df.empty:
        raise ValueError("Correlation file is empty after removing comments.")

    return df


def _build_distance_matrix(df: pd.DataFrame) -> tuple[np.ndarray, List[str]]:
    companies = sorted({*df["company1"].unique(), *df["company2"].unique()})
    index: Dict[str, int] = {company: idx for idx, company in enumerate(companies)}

    size = len(companies)
    distances = np.ones((size, size), dtype=float)
    np.fill_diagonal(distances, 0.0)

    for company1, company2, correlation in df.itertuples(index=False):
        corr = max(min(float(correlation), 1.0), -1.0)
        distance = 1.0 - corr
        i, j = index[company1], index[company2]
        distances[i, j] = distance
        distances[j, i] = distance

    condensed = squareform(distances, checks=False)
    return condensed, companies


def _format_clusters(labels: Iterable[int], companies: List[str]) -> List[List[str]]:
    buckets: Dict[int, List[str]] = defaultdict(list)
    for company, label in zip(companies, labels):
        buckets[int(label)].append(company)

    clusters = [sorted(members) for _, members in sorted(buckets.items(), key=lambda item: (-len(item[1]), item[0]))]
    return clusters


def cluster_companies(
    correlations_file: Path,
    method: str,
    num_clusters: int | None,
    distance_threshold: float | None,
    output: Path | None,
) -> None:
    df = _load_correlations(correlations_file)
    condensed_distances, companies = _build_distance_matrix(df)

    linkage_matrix = linkage(condensed_distances, method=method)

    if num_clusters is not None and distance_threshold is not None:
        raise ValueError("Provide either num_clusters or distance_threshold, not both.")

    if num_clusters is not None:
        labels = fcluster(linkage_matrix, num_clusters, criterion="maxclust")
    else:
        threshold = distance_threshold if distance_threshold is not None else 0.6
        labels = fcluster(linkage_matrix, threshold, criterion="distance")

    clusters = _format_clusters(labels, companies)

    if output is not None:
        with open(output, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["cluster", "company"])
            for cluster_id, members in enumerate(clusters, start=1):
                for company in members:
                    writer.writerow([cluster_id, company])

    print(
        f"Generated {len(clusters)} clusters from {len(companies)} companies using method='{method}'."
    )
    for cluster_id, members in enumerate(clusters, start=1):
        print(f"\nCluster {cluster_id} ({len(members)} companies):")
        for company in members:
            print(f"  - {company}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cluster companies based on correlation scores.")
    parser.add_argument(
        "correlations",
        type=Path,
        help="Path to correlations CSV (company1,company2,correlation).",
    )
    parser.add_argument(
        "--method",
        default="average",
        choices=["single", "complete", "average", "weighted", "ward"],
        help="Linkage method for hierarchical clustering.",
    )
    parser.add_argument(
        "--clusters",
        type=int,
        help="Target number of clusters (overrides distance threshold).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        help="Maximum merge distance when forming clusters (ignored if --clusters supplied).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional CSV path to write company-to-cluster assignments.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cluster_companies(
        correlations_file=args.correlations,
        method=args.method,
        num_clusters=args.clusters,
        distance_threshold=args.threshold,
        output=args.output,
    )


if __name__ == "__main__":
    main()
