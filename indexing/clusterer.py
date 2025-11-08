"""Adaptive KMeans clustering with silhouette scoring."""
import logging
import numpy as np
from typing import Dict, Any
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from config import CLUSTER_RANGE

logger = logging.getLogger(__name__)


class AdaptiveClusterer:
    """Performs adaptive KMeans clustering to find optimal k."""

    def cluster(self, embeddings: np.ndarray) -> Dict[str, Any]:
        """
        Cluster embeddings using adaptive KMeans.

        Tries k values in CLUSTER_RANGE and picks the one with best silhouette score.

        Args:
            embeddings: numpy array of shape (n_samples, n_features)

        Returns:
            Dict with keys: labels, n_clusters, silhouette_score, cluster_sizes
        """
        n_samples = embeddings.shape[0]
        min_k, max_k = CLUSTER_RANGE

        # Adjust range if we have fewer samples
        max_k = min(max_k, n_samples - 1)
        min_k = min(min_k, max_k)

        if n_samples < 2:
            logger.warning("Not enough samples for clustering")
            return {
                "labels": np.zeros(n_samples, dtype=int),
                "n_clusters": 1,
                "silhouette_score": 0.0,
                "cluster_sizes": {0: n_samples},
            }

        logger.info(f"Testing k values from {min_k} to {max_k}")

        best_score = -1
        best_k = min_k
        best_labels = None

        for k in range(min_k, max_k + 1):
            # Fit KMeans
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)

            # Calculate silhouette score (only if k > 1)
            if k > 1 and n_samples > k:
                score = silhouette_score(embeddings, labels)
                logger.info(f"k={k}: silhouette_score={score:.4f}")

                if score > best_score:
                    best_score = score
                    best_k = k
                    best_labels = labels
            else:
                best_labels = labels

        # Calculate cluster sizes
        unique, counts = np.unique(best_labels, return_counts=True)
        cluster_sizes = {int(label): int(count) for label, count in zip(unique, counts)}

        logger.info(
            f"Optimal clustering: k={best_k}, silhouette={best_score:.4f}, "
            f"sizes={cluster_sizes}"
        )

        return {
            "labels": best_labels,
            "n_clusters": best_k,
            "silhouette_score": float(best_score),
            "cluster_sizes": cluster_sizes,
        }
