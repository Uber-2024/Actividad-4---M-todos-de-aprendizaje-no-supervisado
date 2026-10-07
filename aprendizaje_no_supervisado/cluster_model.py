"""Compara métodos de aprendizaje no supervisado para agrupar viajes.

La lógica principal consiste en cargar el dataset sintético, preparar las
características numéricas, aplicar varios algoritmos de clustering y guardar
métricas de calidad para comparar su rendimiento.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Rutas del dataset y de los artefactos generados por el clustering.
PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "trips.csv"
OUTPUT_DIR = PROJECT_DIR / "artifacts"

# Columna oculta: nunca se incluye en FEATURES para el agrupamiento.
HIDDEN_LABEL = "trip_profile"

# Variables numéricas que los algoritmos usan para formar grupos.
NUMERIC_FEATURES = [
    "planned_minutes",
    "departure_hour",
    "weekday",
    "is_weekend",
    "rain_mm",
    "occupancy_level",
    "incident",
    "transfers",
    "actual_minutes",
]
FEATURES = NUMERIC_FEATURES

# Número de grupos pedido a K-Means y al clustering aglomerativo.
N_CLUSTERS = 3


def create_preprocessor() -> ColumnTransformer:
    """Prepara el flujo de transformación de características numéricas.

    Returns:
        Un ColumnTransformer que imputa valores faltantes y normaliza las columnas.
    """
    # Imputación por mediana y escalado para que todas las variables pesen igual.
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer([("numeric", numeric_pipeline, NUMERIC_FEATURES)])


def evaluate_clustering(features, labels) -> dict[str, float | int]:
    """Calcula métricas de calidad de agrupamiento.

    Args:
        features: matriz de características transformadas.
        labels: etiquetas de cluster asignadas (-1 indica ruido en DBSCAN).

    Returns:
        Diccionario con número de clusters, puntos de ruido, silueta,
        Calinski-Harabasz y Davies-Bouldin.
    """
    # Se ignoran las etiquetas de ruido (-1) al contar clusters válidos.
    unique_labels = sorted({int(label) for label in labels if int(label) != -1})
    n_clusters = len(unique_labels)
    n_noise = int(sum(1 for label in labels if int(label) == -1))

    # Con menos de dos grupos no se pueden calcular métricas de separación.
    if n_clusters < 2:
        return {
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "silhouette": 0.0,
            "calinski_harabasz": 0.0,
            "davies_bouldin": 999.0,
        }

    # Se filtran los puntos de ruido antes de evaluar la calidad.
    mask = [int(label) != -1 for label in labels]
    filtered_features = features[mask]
    filtered_labels = [int(label) for label, keep in zip(labels, mask) if keep]

    return {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "silhouette": round(float(silhouette_score(filtered_features, filtered_labels)), 4),
        "calinski_harabasz": round(
            float(calinski_harabasz_score(filtered_features, filtered_labels)), 3
        ),
        "davies_bouldin": round(
            float(davies_bouldin_score(filtered_features, filtered_labels)), 4
        ),
    }


def cluster_and_evaluate() -> dict[str, dict[str, float | int]]:
    """Aplica los algoritmos de clustering y genera el reporte de resultados.

    Returns:
        Un diccionario con las métricas por método: K-Means, aglomerativo y DBSCAN.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DATA_PATH}. Ejecute primero generate_dataset.py."
        )

    # Carga del dataset y transformación de las variables numéricas.
    data = pd.read_csv(DATA_PATH)
    preprocessor = create_preprocessor()
    features = preprocessor.fit_transform(data[FEATURES])

    # Definición de los tres métodos que se comparan en la evaluación.
    models = {
        "kmeans": KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10),
        "agglomerative": AgglomerativeClustering(n_clusters=N_CLUSTERS),
        "dbscan": DBSCAN(eps=1.4, min_samples=12),
    }

    results: dict[str, dict[str, float | int]] = {}
    cluster_assignments: dict[str, list[int]] = {}
    for name, model in models.items():
        # fit_predict agrupa y devuelve la etiqueta de cada viaje.
        labels = model.fit_predict(features)
        results[name] = evaluate_clustering(features, labels)
        cluster_assignments[name] = [int(label) for label in labels]

    # Persistencia de artefactos para análisis posterior y para la interfaz web.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"preprocessor": preprocessor, "model": models["kmeans"]},
        OUTPUT_DIR / "kmeans.joblib",
    )

    # Se guarda una copia del CSV con el cluster de K-Means añadido.
    labeled_data = data.copy()
    labeled_data["cluster_kmeans"] = cluster_assignments["kmeans"]
    labeled_data.to_csv(OUTPUT_DIR / "trips_clustered.csv", index=False)

    report = {
        "dataset": str(DATA_PATH.relative_to(PROJECT_DIR)),
        "rows": len(data),
        "features": FEATURES,
        "hidden_label": HIDDEN_LABEL,
        "n_clusters_requested": N_CLUSTERS,
        "data_origin": "synthetic, generated from network.json with latent trip profiles",
        "models": results,
        "interpretation": {
            "silhouette": "Más alto es mejor (mejor separación entre grupos).",
            "calinski_harabasz": "Más alto es mejor (grupos compactos y separados).",
            "davies_bouldin": "Más bajo es mejor (menos solapamiento entre grupos).",
        },
    }
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return results


if __name__ == "__main__":
    # Muestra las métricas de cada método al ejecutar este archivo de forma directa.
    for model_name, metrics in cluster_and_evaluate().items():
        print(
            f"{model_name}: clusters={metrics['n_clusters']} | "
            f"silueta={metrics['silhouette']} | "
            f"CH={metrics['calinski_harabasz']} | "
            f"DB={metrics['davies_bouldin']}"
        )
