from geopy.distance import geodesic
from geopy.point import Point as GeopyPoint
import googlemaps
import os
import time
import math
import numpy as np
from shapely.geometry import Point, LineString, Polygon

from properties.src.apis.google_maps import GoogleMaps
from shared.utils.constants import EARTH_RADIUS


def calculate_bearing(lat1, lon1, lat2, lon2):
    # calcular o rumo entre dois pontos geográficos
    lat1, lon1, lat2, lon2 = (
        math.radians(lat1),
        math.radians(lon1),
        math.radians(lat2),
        math.radians(lon2),
    )
    dLon = lon2 - lon1
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
        lat2
    ) * math.cos(dLon)
    bearing = math.atan2(x, y)
    return math.degrees(bearing)


def calculate_midpoint(lat1, lon1, lat2, lon2):
    # calcular os pontos médios entre dois pontos
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)
    distance = geodesic((lat1, lon1), (lat2, lon2)).meters / 2
    midpoint = calculate_destination_point_front(lat1, lon1, bearing, distance)
    return midpoint


def generate_polygon_with_midpoints(points):
    # gerar o polígono com pontos médios
    detailed_points = []
    num_points = len(points)
    for i in range(num_points):
        detailed_points.append(points[i])
        mid_lat, mid_lon = calculate_midpoint(
            points[i][0],
            points[i][1],
            points[(i + 1) % num_points][0],
            points[(i + 1) % num_points][1],
        )
        detailed_points.append((mid_lat, mid_lon))
    return detailed_points


def order_rectangle_corners(corners):
    # assume que corners[0] é o ponto de início
    # encontra os cantos com base nas distâncias euclidianas
    # ordena primeiro por y (longitude) e depois por x (latitude) para obter uma ordem de caminhada
    sorted_by_y = sorted(corners, key=lambda x: x[1])
    lower = sorted(sorted_by_y[:2], key=lambda x: x[0])
    upper = sorted(sorted_by_y[2:], key=lambda x: x[0], reverse=True)
    return lower + upper


def find_corners(line1, line2, line3):
    points_line1 = set(line1)
    points_line2 = set(line2)
    points_line3 = set(line3)

    shared_point1 = list(points_line1 & points_line2)[0]
    shared_point2 = list(points_line1 & points_line3)[0]

    non_shared_point1 = list(points_line2 - {shared_point1})[0]
    non_shared_point2 = list(points_line3 - {shared_point2})[0]

    # usar a função order_rectangle_corners para organizar os cantos corretamente
    corners = [
        shared_point1,
        non_shared_point1,
        shared_point2,
        non_shared_point2,
    ]
    return order_rectangle_corners(corners)


def generate_line_points_front(points, length, spacing):
    # gerar um conjunto de pontos a partir de uma reta inicial e que contém o comprimento passado e a direção da mesma reta inicial

    # determinar o ponto médio da linha original
    lat1, lon1 = points[0]
    lat2, lon2 = points[-1]
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2

    # calcular o rumo da linha do primeiro ao último ponto
    bearing = math.degrees(
        math.atan2(
            math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2)),
            math.cos(math.radians(lat1)) * math.sin(math.radians(lat2))
            - math.sin(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.cos(math.radians(lon2 - lon1)),
        )
    )

    # calcular os pontos ao longo da nova linha centrada no ponto médio
    num_points = int(length / spacing)
    new_points = []
    for i in range(num_points + 1):
        dist_from_mid = spacing * (i - num_points / 2)
        new_lat, new_lon = calculate_destination_point_front(
            mid_lat, mid_lon, bearing, dist_from_mid
        )
        new_points.append((new_lat, new_lon))

    return new_points


def calculate_destination_point_front(lat, lon, bearing, distance):
    bearing = math.radians(bearing)

    lat = math.radians(lat)
    lon = math.radians(lon)

    lat2 = math.asin(
        math.sin(lat) * math.cos(distance / EARTH_RADIUS)
        + math.cos(lat) * math.sin(distance / EARTH_RADIUS) * math.cos(bearing)
    )
    lon2 = lon + math.atan2(
        math.sin(bearing) * math.sin(distance / EARTH_RADIUS) * math.cos(lat),
        math.cos(distance / EARTH_RADIUS) - math.sin(lat) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def calculate_points(lat, lon, distance=10, num_points=4):
    # calcular pontos para frente e para trás

    gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY_ELEVATION"))
    points = []

    # converter distância em graus de latitude/longitude aproximados
    lon_change = distance / (
        111320 * math.cos(lat * math.pi / 180)
    )  # ajuste para longitude

    # gerar pontos temporários
    for direction in [1, -1]:  # 1 para frente, -1 para trás
        for i in range(1, num_points + 1):
            new_lat = lat
            new_lon = lon + (lon_change * i * direction)
            points.append((new_lat, new_lon))

    # inserir o ponto inicial no centro para incluir no processamento do snapToRoads
    points.insert(num_points, (lat, lon))

    # usar snapToRoads para ajustar os pontos à rua mais próxima
    path = gmaps.snap_to_roads(points, interpolate=True)
    road_points = [
        (point["location"]["latitude"], point["location"]["longitude"])
        for point in path
    ]

    return road_points


def calculate_dimensions(area):
    # limite frontal
    front = min(60, max(12, 45 if area >= 1700 else (area / 1700) * 28 + 12))
    depth = area / front
    return front, depth


def calculate_parallel_lines(points, distance_between_lines):
    left_line = []
    right_line = []

    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i + 1]

        # calcular o rumo do segmento atual
        bearing = calculate_bearing(lat1, lon1, lat2, lon2)

        # calcular as linhas paralelas para cada ponto
        for point in [points[i], points[i + 1]]:
            left_point = geodesic(meters=distance_between_lines).destination(
                point, bearing + 90
            )
            right_point = geodesic(meters=distance_between_lines).destination(
                point, bearing - 90
            )
            left_line.append((left_point.latitude, left_point.longitude))
            right_line.append((right_point.latitude, right_point.longitude))

    # evitar duplicação do último ponto
    left_line = list(dict.fromkeys(left_line))
    right_line = list(dict.fromkeys(right_line))

    return left_line, right_line


def find_closest_line(lat, lon, left_line, right_line):
    """
    Calcula e retorna qual das duas linhas, esquerda ou direita, está mais próxima de um ponto dado.

    Args:
    point (tuple): A tupla (latitude, longitude) do ponto de interesse.
    left_line (list): Lista de tuplas (latitude, longitude) que define a linha à esquerda.
    right_line (list): Lista de tuplas (latitude, longitude) que define a linha à direita.

    Returns:
    str: Retorna 'left' se a linha esquerda estiver mais próxima, 'right' se a linha direita estiver mais próxima.
    """
    # criar um objeto Point para o ponto de interesse
    point_geom = Point(lat, lon)  # Shapely usa a ordem (longitude, latitude)

    # criar objetos LineString para as linhas esquerda e direita
    left_line_geom = LineString([(lon, lat) for lat, lon in left_line])
    right_line_geom = LineString([(lon, lat) for lat, lon in right_line])

    # calcular a distância do ponto às duas linhas
    dist_to_left = point_geom.distance(left_line_geom)
    dist_to_right = point_geom.distance(right_line_geom)

    # determinar qual linha está mais próxima
    if dist_to_left < dist_to_right:
        return "left"
    else:
        return "right"


def geodesic_rectangle_points(center_line, orientation, depth):
    # extrair os pontos das retas
    start_point = GeopyPoint(center_line[0])
    end_point = GeopyPoint(center_line[-1])

    # calcular o ângulo da linha em relação ao Norte
    latitude_difference = end_point.latitude - start_point.latitude
    longitude_difference = end_point.longitude - start_point.longitude
    center_angle = math.degrees(
        math.atan2(longitude_difference, latitude_difference)
    )

    # definir o ângulo das linhas perpendiculares
    if orientation == "left":
        perp_angle = (center_angle + 90) % 360
    elif orientation == "right":
        perp_angle = (center_angle - 90) % 360
    else:
        raise ValueError("Orientation must be 'left' or 'right'")

    # calcular os pontos finais das retas perpendiculares para os dois extremos da linha central
    p1_end = geodesic(meters=depth).destination(start_point, perp_angle)
    p2_end = geodesic(meters=depth).destination(end_point, perp_angle)

    # retornar os pontos como tuples de coordenadas (latitude, longitude)
    return [
        (start_point.latitude, start_point.longitude),
        (p1_end.latitude, p1_end.longitude),
    ], [
        (end_point.latitude, end_point.longitude),
        (p2_end.latitude, p2_end.longitude),
    ]


def get_lot_points(
    lat: float, lon: float, area: float, spacing: int, distancia: int
):
    dimensions = calculate_dimensions(area)
    front = dimensions[0]
    depth = dimensions[1]

    center_line = calculate_points(lat, lon, distance=distancia, num_points=4)

    new_line_points = generate_line_points_front(center_line, front, spacing)

    left_line, right_line = calculate_parallel_lines(center_line, distancia)

    closest_line = find_closest_line(lat, lon, left_line, right_line)

    perpendicular_lines = geodesic_rectangle_points(
        new_line_points, closest_line, depth
    )
    points = find_corners(
        new_line_points, perpendicular_lines[0], perpendicular_lines[1]
    )

    detailed_polygon_points = generate_polygon_with_midpoints(points)

    return detailed_polygon_points


def generate_points_in_polygon(polygon, num_points):
    # gerar pontos aleatórios dentro de um polígono

    minx, miny, maxx, maxy = polygon.bounds
    points = []
    while len(points) < num_points:
        point = Point(
            np.random.uniform(minx, maxx), np.random.uniform(miny, maxy)
        )
        if polygon.contains(point):
            points.append(
                (point.y, point.x)
            )  # Shapely usa (x, y) mas precisamos de (lat, lon)
    return points


def get_lot_volume(polygon_points, num_points=500):
    try:
        google_maps_api = GoogleMaps()

        # Extract lat and lon from GeographicalPoint instances
        polygon = Polygon([(point.lon, point.lat) for point in polygon_points])

        random_points = generate_points_in_polygon(polygon, num_points)

        elevation_data = []
        for lat, lon in random_points:
            result = google_maps_api.get_elevation(lat, lon)
            if result["error"] is None:
                elevation_data.append((lat, lon, result["elevation"]))
            time.sleep(0.3)

        if not elevation_data:
            error_message = (
                "Nenhum dado de elevação válido disponível para interpolação."
            )
            return {"error": error_message}, 0
        else:
            lats_valid, lons_valid, elevations_valid = zip(*elevation_data)

            lons_valid = np.array(lons_valid)
            lats_valid = np.array(lats_valid)
            elevations_valid = np.array(elevations_valid)

            min_elevation = min(elevations_valid)
            max_elevation = max(elevations_valid)
            elevation_difference = max_elevation - min_elevation
            return elevation_data, elevation_difference
    except Exception as e:
        return {"error": str(e)}, 0
