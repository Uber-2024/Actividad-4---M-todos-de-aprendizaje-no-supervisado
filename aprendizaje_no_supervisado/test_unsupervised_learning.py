"""Pruebas del flujo de aprendizaje no supervisado del proyecto."""

import unittest

import pandas as pd

from generate_dataset import FIELDNAMES, PROFILES, generate_dataset
from cluster_model import FEATURES, HIDDEN_LABEL, cluster_and_evaluate


class UnsupervisedLearningTests(unittest.TestCase):
    """Valida que el dataset y el clustering cumplen los requisitos básicos."""

    @classmethod
    def setUpClass(cls):
        """Genera el dataset una sola vez antes de ejecutar las pruebas de la clase."""
        cls.dataset_path = generate_dataset()
        cls.dataset = pd.read_csv(cls.dataset_path)

    def test_dataset_has_expected_shape_and_profiles(self):
        """Comprueba que el CSV tiene la estructura esperada y perfiles latentes.

        Verifica columnas, cantidad de filas, coherencia de duraciones y
        presencia de los tres perfiles ocultos del dataset.
        """
        self.assertEqual(list(self.dataset.columns), FIELDNAMES)
        self.assertEqual(len(self.dataset), 1200)
        # La duración real nunca debería ser menor que la planificada.
        self.assertTrue((self.dataset["actual_minutes"] >= self.dataset["planned_minutes"]).all())
        self.assertEqual(set(self.dataset["trip_profile"]), set(PROFILES))

    def test_clustering_uses_only_available_features_without_hidden_label(self):
        """Verifica que el clustering no usa la etiqueta oculta y produce métricas válidas.

        Confirma que trip_profile no está en FEATURES, que existen los tres
        métodos esperados y que K-Means obtiene una silueta positiva.
        """
        self.assertNotIn(HIDDEN_LABEL, FEATURES)
        results = cluster_and_evaluate()
        self.assertEqual(set(results), {"kmeans", "agglomerative", "dbscan"})
        for metrics in results.values():
            self.assertIn("silhouette", metrics)
            self.assertGreaterEqual(metrics["n_clusters"], 1)
        self.assertGreater(results["kmeans"]["silhouette"], 0)


if __name__ == "__main__":
    # Permite ejecutar las pruebas con: python test_unsupervised_learning.py
    unittest.main()
