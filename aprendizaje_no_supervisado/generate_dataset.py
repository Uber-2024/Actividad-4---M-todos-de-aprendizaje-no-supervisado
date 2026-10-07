"""Genera un conjunto sintético de viajes para métodos de aprendizaje no supervisado.

Este módulo toma la red base de transporte, calcula rutas planificadas y
crea un dataset reproducible con perfiles latentes de viaje. Los algoritmos
de agrupamiento descubrirán esos grupos sin usar la etiqueta oculta.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

# Se añade la raíz del proyecto al path para importar el planificador de rutas.
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import Connection, RoutePlanner  # noqa: E402

# Rutas y parámetros por defecto del dataset sintético.
DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_PATH = DATA_DIR / "trips.csv"
NETWORK_PATH = ROOT_DIR / "network.json"
SAMPLE_SIZE = 1200
SEED = 2026

# Columnas del CSV, en el mismo orden en que se escriben.
FIELDNAMES = [
    "origin",
    "destination",
    "planned_minutes",
    "departure_hour",
    "weekday",
    "is_weekend",
    "rain_mm",
    "occupancy_level",
    "incident",
    "transfers",
    "actual_minutes",
    "trip_profile",
]

# Perfiles latentes que el clustering debería recuperar sin ver esta columna.
PROFILES = ("hora_punta", "viaje_tranquilo", "viaje_con_incidencia")


def build_route_options() -> list[dict[str, object]]:
    """Calcula todos los pares de estaciones conectados y sus rutas planificadas.

    Returns:
        Una lista con el origen, destino, tiempo planificado y número de transbordos
        de cada conexión válida dentro de la red.
    """
    # Se carga la red JSON y se construye el planificador de rutas.
    network = json.loads(NETWORK_PATH.read_text(encoding="utf-8"))
    stations = [station["name"] for station in network["stations"]]
    connections = [Connection(**item) for item in network["connections"]]
    planner = RoutePlanner()
    routes: list[dict[str, object]] = []

    # Se evalúa cada combinación posible de estaciones para generar rutas válidas.
    for origin in stations:
        for destination in stations:
            if origin == destination:
                continue
            try:
                segments, planned_minutes = planner.find_route(
                    connections, origin, destination
                )
            except ValueError:
                # Si no hay camino disponible, se descarta la combinación.
                continue
            routes.append(
                {
                    "origin": origin,
                    "destination": destination,
                    "planned_minutes": planned_minutes,
                    # Un cambio de línea cuenta como un transbordo.
                    "transfers": max(0, len({segment.line for segment in segments}) - 1),
                }
            )
    return routes


def sample_trip_conditions(
    profile: str, transfers: int, rng: random.Random
) -> dict[str, int]:
    """Genera condiciones operativas coherentes con un perfil latente de viaje.

    Args:
        profile: nombre del perfil latente (hora punta, tranquilo o con incidencia).
        transfers: número de transbordos de la ruta elegida.
        rng: generador aleatorio con semilla fija para reproducibilidad.

    Returns:
        Diccionario con hora, día, lluvia, ocupación e incidencia simuladas.
    """
    # Cada perfil fuerza un patrón distinto de hora, clima y ocupación.
    if profile == "hora_punta":
        hour = rng.choice([7, 8, 9, 16, 17, 18])
        weekday = rng.randrange(5)
        rain_mm = rng.choices(range(0, 8), weights=[5, 4, 3, 2, 1, 1, 1, 1])[0]
        occupancy = rng.choices(range(3, 6), weights=[2, 4, 4])[0]
        incident = int(rng.random() < 0.04)
    elif profile == "viaje_tranquilo":
        hour = rng.choice([10, 11, 12, 13, 14, 15, 20, 21, 22])
        weekday = rng.randrange(7)
        rain_mm = rng.choices(range(0, 6), weights=[8, 5, 3, 2, 1, 1])[0]
        occupancy = rng.choices(range(1, 4), weights=[4, 4, 2])[0]
        incident = 0
    else:
        # Perfil con incidencia: siempre hay un evento que retrasa el viaje.
        hour = rng.randrange(24)
        weekday = rng.randrange(7)
        rain_mm = rng.choices(range(2, 21), weights=[1] * 8 + [2] * 11)[0]
        occupancy = rng.choices(range(2, 6), weights=[2, 3, 3, 2])[0]
        incident = 1

    return {
        "departure_hour": hour,
        "weekday": weekday,
        "is_weekend": int(weekday >= 5),
        "rain_mm": rain_mm,
        "occupancy_level": occupancy,
        "incident": incident,
        "transfers": transfers,
    }


def synthetic_trip_duration(
    planned_minutes: int,
    departure_hour: int,
    rain_mm: int,
    occupancy_level: int,
    incident: int,
    transfers: int,
    rng: random.Random,
) -> int:
    """Simula una duración observada de viaje con condiciones operativas plausibles.

    Esta función no usa datos reales; solo genera valores sintéticos con un
    comportamiento similar al de un sistema de transporte con congestión y retrasos.

    Args:
        planned_minutes: duración planificada de la ruta.
        departure_hour: hora de salida (0-23).
        rain_mm: milímetros de lluvia simulados.
        occupancy_level: nivel de ocupación del 1 al 5.
        incident: 1 si hay incidencia, 0 si no.
        transfers: número de transbordos.
        rng: generador aleatorio reproducible.

    Returns:
        Duración observada redondeada, nunca menor que el tiempo planificado.
    """
    # La congestión aumenta en horas pico.
    rush_hour = departure_hour in {7, 8, 9, 16, 17, 18}
    congestion = rng.uniform(0.08, 0.28) if rush_hour else rng.uniform(0, 0.12)
    delay = (
        planned_minutes * congestion
        + rain_mm * 0.35
        + max(0, occupancy_level - 2) * 1.1
        + incident * rng.uniform(5, 18)
        + transfers * 1.5
        + rng.gauss(0, 2.5)
    )
    return max(planned_minutes, round(planned_minutes + delay))


def generate_dataset(sample_size: int = SAMPLE_SIZE, seed: int = SEED) -> Path:
    """Escribe el CSV del conjunto sintético con una semilla fija.

    Args:
        sample_size: número de filas del dataset.
        seed: semilla usada para la reproducibilidad.

    Returns:
        Ruta del archivo CSV generado.
    """
    route_options = build_route_options()
    if not route_options:
        raise ValueError("La red no contiene pares de estaciones conectados.")

    # Semilla fija para que la misma prueba produzca los mismos viajes.
    rng = random.Random(seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _ in range(sample_size):
            # Se elige una ruta válida y un perfil latente al azar.
            route = rng.choice(route_options)
            profile = rng.choice(PROFILES)
            transfers = int(route["transfers"])
            conditions = sample_trip_conditions(profile, transfers, rng)
            planned_minutes = int(route["planned_minutes"])
            writer.writerow(
                {
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "planned_minutes": planned_minutes,
                    **conditions,
                    "actual_minutes": synthetic_trip_duration(
                        planned_minutes,
                        conditions["departure_hour"],
                        conditions["rain_mm"],
                        conditions["occupancy_level"],
                        conditions["incident"],
                        transfers,
                        rng,
                    ),
                    # Etiqueta oculta: no se usa en el clustering.
                    "trip_profile": profile,
                }
            )
    return OUTPUT_PATH


if __name__ == "__main__":
    # Genera el dataset cuando se ejecuta este archivo directamente.
    path = generate_dataset()
    print(f"Dataset generado: {path}")
    print(f"Registros: {SAMPLE_SIZE}; semilla: {SEED}")
