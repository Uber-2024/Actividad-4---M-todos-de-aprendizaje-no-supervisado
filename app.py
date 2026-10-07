"""Módulo principal del backend para calcular rutas en la red de transporte.

Este archivo define el modelo de conexiones y el algoritmo que resuelve
la ruta más corta entre dos estaciones, usando una variante del algoritmo
Dijkstra adaptada para la aplicación de transporte.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Connection:
    """Representa un tramo directo entre dos estaciones del sistema.

    Atributos:
        origin: estación de origen del tramo.
        destination: estación de destino del tramo.
        minutes: duración estimada del trayecto en minutos.
        line: línea o servicio que cubre la conexión.
        accessible: indica si el tramo es accesible para usuarios con movilidad reducida.
    """

    origin: str
    destination: str
    minutes: int
    line: str
    accessible: bool = True


@dataclass(frozen=True)
class Segment:
    """Describe un tramo individual que forma parte de una ruta calculada.

    Se usa para devolver la secuencia exacta de conexiones que componen
    la solución final y facilitar la visualización de la ruta en la interfaz.
    """

    destination: str
    line: str
    minutes: int


class RoutePlanner:
    """Calcula la ruta óptima entre dos estaciones dentro de la red.

    La clase encapsula la lógica de búsqueda del camino más corto y devuelve
    la secuencia detallada de segmentos junto con el tiempo total estimado.
    """

    def find_route(
        self,
        connections: Iterable[Connection],
        origin: str,
        destination: str,
        accessible_only: bool = False,
    ) -> tuple[list[Segment], int]:
        """Obtiene la ruta más corta desde el origen hasta el destino.

        Args:
            connections: lista de conexiones disponibles en la red.
            origin: estación inicial.
            destination: estación final.
            accessible_only: si es True, ignora conexiones no accesibles.

        Returns:
            Una tupla con la lista de segmentos que forman la ruta y el tiempo total.

        Raises:
            ValueError: si no existe una ruta válida entre origen y destino.
        """
        # Si el origen y el destino coinciden, no hay recorrido que calcular.
        if origin == destination:
            return [], 0

        # Se construye un grafo no dirigido conceptual con nodos y aristas ponderadas.
        graph: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
        for connection in connections:
            # Si se exige accesibilidad, se excluyen los tramos inhabilitados.
            if accessible_only and not connection.accessible:
                continue
            graph[connection.origin].append(
                (connection.destination, connection.minutes, connection.line)
            )

        # Si el origen no existe o el destino no es alcanzable, la ruta es inválida.
        if origin not in graph or destination not in graph and destination != origin:
            raise ValueError(f"No existe ruta entre {origin} y {destination}.")

        # Distancia mínima conocida para cada nodo y su previo para reconstrucción.
        distances: dict[str, int] = {origin: 0}
        previous: dict[str, tuple[str, str]] = {}
        queue: list[tuple[int, str]] = [(0, origin)]

        # Búsqueda del camino mínimo usando una estrategia tipo Dijkstra.
        while queue:
            current_distance, current_station = min(queue, key=lambda item: item[0])
            queue.remove((current_distance, current_station))

            if current_station == destination:
                break

            for next_station, travel_time, line in graph.get(current_station, []):
                new_distance = current_distance + travel_time
                if new_distance < distances.get(next_station, float("inf")):
                    distances[next_station] = new_distance
                    previous[next_station] = (current_station, line)
                    queue.append((new_distance, next_station))

        if destination not in distances:
            raise ValueError(f"No existe ruta entre {origin} y {destination}.")

        # Reconstrucción del camino a partir de los nodos anteriores.
        segments: list[Segment] = []
        current = destination
        while current != origin:
            previous_station, line = previous[current]
            travel_time = self._travel_time(connections, previous_station, current)
            segments.append(Segment(destination=current, line=line, minutes=travel_time))
            current = previous_station
        segments.reverse()

        return segments, distances[destination]

    def _travel_time(
        self, connections: Iterable[Connection], origin: str, destination: str
    ) -> int:
        """Devuelve el tiempo de un tramo concreto entre dos estaciones.

        Esta función auxiliar sirve para reconstruir el camino final en términos
        de segmentos individuales y sus tiempos exactos.
        """
        for connection in connections:
            if (
                connection.origin == origin
                and connection.destination == destination
                and connection.accessible
            ):
                return connection.minutes
        raise ValueError(f"No se encontró tramo entre {origin} y {destination}.")
