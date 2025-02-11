import math
import re
from math import radians, sin, cos, sqrt, atan2

# Constante do tamanho padrão dos tiles
TILE_SIZE = 256

def latlon_to_world_pixel(lat, lon, zoom, scale):
    """
    Converte coordenadas geográficas (latitude, longitude) para coordenadas de pixel no mundo.
    """
    sin_lat = math.sin(lat * math.pi / 180)
    map_size = TILE_SIZE * (2 ** zoom) * scale
    x = (lon + 180) / 360 * map_size
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * map_size
    return x, y

def world_pixel_to_latlon(x, y, zoom, scale):
    """
    Converte coordenadas de pixel no mundo para coordenadas geográficas (latitude, longitude).
    """
    map_size = TILE_SIZE * (2 ** zoom) * scale
    lon = (x / map_size) * 360.0 - 180.0
    y_fraction = 0.5 - (y / map_size)
    lat_rad = 2 * math.atan(math.exp(y_fraction * 2 * math.pi)) - math.pi / 2
    lat = lat_rad * 180 / math.pi
    return lat, lon

def get_top_left_world_pixel(center_lat, center_lon, zoom, scale, image_width, image_height):
    """
    Calcula as coordenadas de pixel do canto superior esquerdo da imagem no mundo.
    """
    center_x, center_y = latlon_to_world_pixel(center_lat, center_lon, zoom, scale)
    half_width = image_width / 2
    half_height = image_height / 2
    top_left_x = center_x - half_width
    top_left_y = center_y - half_height
    return top_left_x, top_left_y

def pixel_to_latlon(pixel_x, pixel_y, center_lat, center_lon, zoom, scale, image_width, image_height):
    """
    Converte coordenadas de pixel na imagem para coordenadas geográficas (latitude, longitude).
    
    Parameters:
        pixel_x (int): Coordenada x do pixel na imagem.
        pixel_y (int): Coordenada y do pixel na imagem.
        center_lat (float): Latitude do centro da imagem.
        center_lon (float): Longitude do centro da imagem.
        zoom (int): Nível de zoom.
        scale (int): Fator de escala (ex: 2).
        image_width (int): Largura da imagem em pixels.
        image_height (int): Altura da imagem em pixels.
    
    Returns:
        (lat, lon): Tupla com latitude e longitude correspondentes ao pixel.
    """
    # Calcula as coordenadas do canto superior esquerdo no mundo
    top_left_x, top_left_y = get_top_left_world_pixel(center_lat, center_lon, zoom, scale, image_width, image_height)
    
    # Calcula as coordenadas de pixel no mundo para o pixel dado
    world_x = top_left_x + pixel_x
    world_y = top_left_y + pixel_y
    
    # Converte as coordenadas de pixel no mundo para latitude e longitude
    lat, lon = world_pixel_to_latlon(world_x, world_y, zoom, scale)
    return lat, lon

def extract_zoom(blob_name):
    try:
        # Padrão para identificar o zoom na string (ex: "_19_")
        match = re.search(r"/-?\d+\.\d+_-?\d+\.\d+_(\d+)_", blob_name)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"[ERROR] Falha ao extrair o zoom: {e}")
    # Retorna um padrão se não encontrar
    return 19

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância em metros entre dois pontos usando a fórmula de Haversine.
    """
    R = 6371000  # Raio da Terra em metros
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c
