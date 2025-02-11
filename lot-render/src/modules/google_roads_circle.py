import requests
from typing import List, Dict, Any, Optional, Tuple
import os
from math import sqrt, sin, cos, pi
from collections import defaultdict
import traceback
import time


def calculate_center(points: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calcula o centro do polígono.
    """
    center_lat = sum(p["lat"] for p in points) / len(points)
    center_lng = sum(p["lng"] for p in points) / len(points)
    return {"lat": center_lat, "lng": center_lng}


def calculate_distance(
    point1: Dict[str, float], point2: Dict[str, float]
) -> float:
    """
    Calcula a distância euclidiana entre dois pontos.
    """
    return sqrt(
        (point1["lat"] - point2["lat"]) ** 2
        + (point1["lng"] - point2["lng"]) ** 2
    )


def calculate_max_radius(
    center: Dict[str, float], vertices: List[Dict[str, float]]
) -> float:
    """
    Calcula o maior raio (maior distância entre o centro e qualquer vértice).
    """
    return max(calculate_distance(center, vertex) for vertex in vertices)


def generate_circle_points(
    center: Dict[str, float], radius: float, num_points: int = 15
) -> List[Dict[str, float]]:
    """
    Gera pontos equidistantes sobre uma circunferência.

    Args:
        center: Ponto central do círculo
        radius: Raio do círculo
        num_points: Número de pontos a serem gerados

    Returns:
        Lista de pontos sobre a circunferência
    """
    points = []
    for i in range(num_points):
        # Ângulo em radianos
        angle = (2 * pi * i) / num_points

        # Calcular coordenadas do ponto
        lat = center["lat"] + radius * cos(angle)
        lng = center["lng"] + radius * sin(angle)

        points.append({"lat": lat, "lng": lng})

    return points


def get_place_details(place_id: str) -> Optional[Dict[str, str]]:
    """
    Obtém os detalhes de um lugar usando a API Places do Google.

    Args:
        place_id: ID do lugar no Google Places

    Returns:
        Dicionário com nome da rua e número, se encontrados
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY").split("#")[0].strip()

    try:
        print(f"\nBuscando detalhes para place_id: {place_id}")

        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,address_components,formatted_address",
            "key": api_key,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        result = response.json()
        print(f"Status da resposta Places API: {result.get('status')}")

        if result.get("status") == "OK":
            place_details = result.get("result", {})
            address_components = place_details.get("address_components", [])

            street_info = {"name": None, "number": None}

            # Procurar componentes relevantes
            for component in address_components:
                types = component.get("types", [])
                if "route" in types:
                    street_info["name"] = component.get("long_name")
                elif "street_number" in types:
                    street_info["number"] = component.get("long_name")

            # Se não encontrar nos componentes, usar o nome do lugar
            if not street_info["name"]:
                street_info["name"] = place_details.get("name")

            print(f"Detalhes encontrados: {street_info}")
            return street_info
        else:
            print(f"Erro na resposta da API: {result.get('status')}")
            print(
                f"Mensagem de erro: {result.get('error_message', 'Sem mensagem de erro')}"
            )
            return None

    except Exception as e:
        print(f"Erro ao buscar detalhes do lugar: {str(e)}")
        print(traceback.format_exc())
        return None


def get_street_details(place_details: str) -> Tuple[str, str]:
    """
    Extrai o nome da rua e a numeração.

    Args:
        place_details: Nome completo da rua com numeração (ex: 'R. Esmeralda, 380-440')

    Returns:
        Tupla com (nome da rua, numeração)
    """
    print(f"\nDEBUG - Processando detalhes do endereço: '{place_details}'")

    if not place_details:
        return "Rua desconhecida", ""

    # Separar a rua do número pela vírgula
    parts = place_details.split(",")

    # Nome da rua é a primeira parte
    street_name = parts[0].strip()

    # Número é a segunda parte (se existir)
    number = parts[1].strip() if len(parts) > 1 else ""

    print(f"DEBUG - Nome final da rua: '{street_name}'")
    print(f"DEBUG - Número final: '{number}'")

    return street_name, number


def get_snapped_points(
    points: List[Dict[str, float]],
    interpolate: bool = True,
    use_osrm: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Ajusta pontos à rua mais próxima usando Google Roads API ou OSRM.

    Args:
        points: Lista de dicionários com 'lat' e 'lng'
        interpolate: Se deve interpolar pontos (apenas para Google Roads)
        use_osrm: Se True, usa OSRM em vez do Google Roads

    Returns:
        Optional[Dict[str, Any]]: Dados dos pontos ajustados
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print(
            "Erro: GOOGLE_MAPS_API_KEY não encontrada nas variáveis de ambiente"
        )
        return None

    # Remove qualquer caractere extra da chave
    api_key = api_key.split("#")[0].strip()

    try:
        print("\nChamando serviço de snap to roads...")
        print(f"Serviço selecionado: {'OSRM' if use_osrm else 'Google Roads'}")
        print(f"Total de pontos no path: {len(points)}")

        if use_osrm:
            # Configuração do servidor OSRM
            OSRM_SERVER = "http://34.39.139.68:5000"
            MATCH_ENDPOINT = f"{OSRM_SERVER}/match/v1/driving"

            snapped_points = []
            place_ids = set()

            for point in points:
                lat, lon = point["lat"], point["lng"]
                # Gera um segundo ponto próximo (5 metros na direção norte)
                lat2 = lat + (0.00005)
                lon2 = lon

                # Prepara os pontos para o OSRM (formato: lon,lat)
                coordinates = f"{lon},{lat};{lon2},{lat2}"

                try:
                    # Chamada ao OSRM
                    url = f"{MATCH_ENDPOINT}/{coordinates}?geometries=geojson&overview=full&timestamps=0;1"
                    response = requests.get(url)

                    if response.status_code == 200:
                        data = response.json()
                        if (
                            data["matchings"]
                            and data["matchings"][0]["geometry"]["coordinates"]
                        ):
                            # Pega o primeiro ponto do matching
                            matched_lon, matched_lat = data["matchings"][0][
                                "geometry"
                            ]["coordinates"][0]

                            # Obtém o nome da rua usando o OSRM
                            nearest_url = f"{OSRM_SERVER}/nearest/v1/driving/{matched_lon},{matched_lat}?number=1"
                            nearest_response = requests.get(nearest_url)

                            if nearest_response.status_code == 200:
                                nearest_data = nearest_response.json()
                                if nearest_data["waypoints"]:
                                    street_name = nearest_data["waypoints"][
                                        0
                                    ].get("name", "Rua sem nome")
                                    way_id = str(
                                        nearest_data["waypoints"][0].get(
                                            "way_id", ""
                                        )
                                    )

                                    snapped_point = {
                                        "lat": matched_lat,
                                        "lng": matched_lon,
                                        "placeId": way_id,  # Usando way_id como placeId
                                        "streetName": street_name,
                                    }
                                    snapped_points.append(snapped_point)
                                    place_ids.add(way_id)

                    time.sleep(0.1)  # Pequeno delay entre requisições

                except Exception as e:
                    print(f"Erro ao processar ponto OSRM: {str(e)}")
                    continue

            return {
                "snapped_points": snapped_points,
                "streets_info": [
                    {"name": point["streetName"], "place_id": point["placeId"]}
                    for point in snapped_points
                    if "streetName" in point
                ],
            }

        else:
            # Código original do Google Roads API
            path = "|".join([f"{p['lat']},{p['lng']}" for p in points])
            params = {
                "path": path,
                "interpolate": str(interpolate).lower(),
                "key": api_key,
            }

            response = requests.get(
                "https://roads.googleapis.com/v1/snapToRoads", params=params
            )

            if response.status_code != 200:
                print(
                    f"Erro na resposta da API (Status: {response.status_code})"
                )
                print(f"Resposta: {response.text}")
                return None

            result = response.json()

            print("\nResposta detalhada da API Roads:")
            print(f"Dados recebidos: {result.keys()}")

            if "snappedPoints" not in result:
                print("Erro: Nenhum ponto ajustado retornado pela API")
                print(f"Resposta da API: {result}")
                return None

            # Imprimir detalhes dos pontos ajustados
            print("\nDetalhes dos pontos ajustados:")
            for i, point in enumerate(result["snappedPoints"]):
                print(f"\nPonto {i + 1}:")
                print(f"- Latitude: {point['location']['latitude']}")
                print(f"- Longitude: {point['location']['longitude']}")
                if "placeId" in point:
                    print(f"- Place ID: {point['placeId']}")
                if "originalIndex" in point:
                    print(f"- Índice original: {point['originalIndex']}")

            snapped_points = []
            place_ids = set()  # Usar set para evitar duplicatas

            for point in result["snappedPoints"]:
                snapped_point = {
                    "lat": point["location"]["latitude"],
                    "lng": point["location"]["longitude"],
                }

                # Verificar se tem placeId
                if "placeId" in point:
                    snapped_point["placeId"] = point["placeId"]
                    place_ids.add(point["placeId"])

                snapped_points.append(snapped_point)

            print(f"\nResumo do processamento:")
            print(f"- Total de pontos ajustados: {len(snapped_points)}")
            print(f"- Total de placeIds únicos: {len(place_ids)}")

            if place_ids:
                print("\nPlaceIds encontrados:")
                for place_id in place_ids:
                    print(f"  • {place_id}")
                    # Tentar obter detalhes do lugar
                    try:
                        place_details = get_place_details(place_id)
                        print(
                            f"    - Nome da rua: {place_details if place_details else 'Não encontrado'}"
                        )
                    except Exception as e:
                        print(f"    - Erro ao buscar detalhes: {str(e)}")

            # Buscar detalhes das ruas para cada placeId único
            streets_info = []
            for place_id in place_ids:
                street_details = get_place_details(place_id)
                if street_details and street_details["name"]:
                    # Contar quantos pontos usam este placeId
                    points_count = sum(
                        1
                        for p in result["snappedPoints"]
                        if "placeId" in p and p["placeId"] == place_id
                    )

                    streets_info.append(
                        {
                            "name": street_details["name"],
                            "number": street_details.get("number"),
                            "place_id": place_id,
                            "total_points": points_count,
                        }
                    )
                    print(
                        f"- Rua encontrada: {street_details['name']} "
                        f"({points_count} pontos)"
                        f"{' - Número: ' + street_details['number'] if street_details.get('number') else ''}"
                    )

            return {
                "snapped_points": snapped_points,
                "streets_info": streets_info,
            }

    except Exception as e:
        print(f"Erro ao chamar serviço de snap to roads: {e}")
        print(traceback.format_exc())
        return None


def process_lot_circle(
    coordinates: List[Dict[str, float]], num_points: int = 7
) -> Dict[str, Any]:
    """
    Processa um lote gerando pontos em círculo e encontrando ruas próximas.
    """
    try:
        # Calcular centro e gerar pontos
        center = calculate_center(coordinates)
        radius = calculate_max_radius(center, coordinates)
        circle_points = generate_circle_points(center, radius, num_points)

        # Obter pontos ajustados à rua
        roads_data = get_snapped_points(circle_points)
        if not roads_data or not roads_data["snapped_points"]:
            print("ERRO: Nenhum ponto ajustado à rua encontrado")
            return {
                "success": False,
                "error": "Falha ao obter pontos ajustados à rua",
            }

        # Se chegou aqui, temos pontos ajustados
        return {
            "success": True,
            "center": center,
            "radius": radius,
            "circle_points": circle_points,
            "snapped_points": roads_data["snapped_points"],
            "streets_info": roads_data["streets_info"],
        }

    except Exception as e:
        print(f"Erro ao processar círculo do lote: {str(e)}")
        return {"success": False, "error": str(e)}
