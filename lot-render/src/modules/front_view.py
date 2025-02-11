import folium
from folium import plugins
from typing import List, Dict, Any, Union

def create_satellite_map(center_lat: float, center_lon: float, zoom: int = 19) -> folium.Map:
    """
    Cria um mapa base com visualização de satélite.
    """
    return folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        control_scale=True
    )

def add_lot_polygon(map_obj: folium.Map, coordinates: List[Dict[str, float]], color: str = 'blue') -> folium.Map:
    """
    Adiciona o polígono do lote ao mapa.
    """
    locations = [[point['lat'], point['lng']] for point in coordinates]
    
    folium.Polygon(
        locations=locations,
        color=color,
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.2,
        popup='Lote'
    ).add_to(map_obj)
    
    # Adicionar vértices do polígono
    for i, point in enumerate(coordinates):
        folium.CircleMarker(
            location=[point['lat'], point['lng']],
            radius=3,
            color='blue',
            fill=True,
            popup=f'Vértice {i}'
        ).add_to(map_obj)
    
    return map_obj

def visualize_lot_front(result: Dict[str, Any], output_path: str = 'output/front_detection.html') -> None:
    """
    Visualiza o lote com todos os elementos da detecção de frente.
    """
    if not result:
        print("Resultado inválido para visualização")
        return
    
    # Calcular centro do lote para o mapa
    coords = result['lot_coordinates']
    center_lat = sum(p['lat'] for p in coords) / len(coords)
    center_lng = sum(p['lng'] for p in coords) / len(coords)
    
    # Criar mapa
    m = create_satellite_map(center_lat, center_lng)
    
    # Adicionar polígono do lote e seus vértices
    m = add_lot_polygon(m, result['lot_coordinates'])
    
    # Adicionar pontos snapados (vermelhos)
    for point in result['snapped_points']:
        folium.CircleMarker(
            location=[point['lat'], point['lng']],
            radius=3,
            color='red',
            fill=True,
            popup='Ponto na Rua'
        ).add_to(m)
    
    # Destacar vértices da frente (amarelos e maiores)
    for i, vertex in enumerate(result['front_vertices']):
        folium.CircleMarker(
            location=[vertex['lat'], vertex['lng']],
            radius=6,
            color='yellow',
            fill=True,
            popup=f'Frente do Lote - Vértice {result["front_vertex_indices"][i]}'
        ).add_to(m)
    
    # Adicionar legenda
    legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    border:2px solid grey; z-index:9999; 
                    background-color:white;
                    padding: 10px;
                    font-size: 14px;">
            <p><span style="color: blue;">●</span> Vértices do Lote</p>
            <p><span style="color: red;">●</span> Pontos na Rua</p>
            <p><span style="color: yellow;">●</span> Frente do Lote</p>
        </div>
        '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Adicionar minimap e controles
    plugins.MiniMap().add_to(m)
    folium.LayerControl().add_to(m)
    
    # Salvar mapa
    m.save(output_path)
    print(f"Mapa salvo em: {output_path}") 