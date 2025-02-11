import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Função para encontrar a cor média de pontos próximos não escuros
def get_replacement_color(point, data, radius=2.0):
    x, y, z = point['x'], point['y'], point['z']
    # Filtrar pontos próximos
    nearby_points = data[
        (~data['is_dark']) &  # Apenas pontos não escuros
        (np.abs(data['x'] - x) <= radius) & 
        (np.abs(data['y'] - y) <= radius) &
        (np.abs(data['z'] - z) <= radius)
    ]
    if nearby_points.empty:
        return None  # Nenhum ponto próximo encontrado
    # Calcular a média de R, G, B dos pontos próximos
    avg_r = nearby_points['r'].mean()
    avg_g = nearby_points['g'].mean()
    avg_b = nearby_points['b'].mean()
    return int(avg_r), int(avg_g), int(avg_b)

# Função para corrigir cores escuras
def correct_dark_colors(data, dark_threshold=50, radius=2.0):
    data['is_dark'] = data[['r', 'g', 'b']].mean(axis=1) < dark_threshold
    for index, row in data[data['is_dark']].iterrows():
        replacement_color = get_replacement_color(row, data, radius)
        if replacement_color:
            data.loc[index, ['r', 'g', 'b']] = replacement_color
    # Atualizar a coluna 'hex_color'
    data['hex_color'] = data.apply(lambda row: f"#{int(row['r']):02x}{int(row['g']):02x}{int(row['b']):02x}", axis=1)
    return data

# Função para plotar os pontos antes e depois da correção
def plot_points_before_after(data_original, data_corrected):
    point_size = 10
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('Comparação: Antes e Depois da Correção de Cores', fontsize=16)

    # Plot original
    axes[0].scatter(
        data_original['x'], data_original['y'],
        c=data_original['hex_color'],
        s=point_size,
        edgecolor='none'
    )
    axes[0].set_title('Antes da Correção')
    axes[0].set_xlabel('X')
    axes[0].set_ylabel('Y')

    # Plot corrigido
    axes[1].scatter(
        data_corrected['x'], data_corrected['y'],
        c=data_corrected['hex_color'],
        s=point_size,
        edgecolor='none'
    )
    axes[1].set_title('Depois da Correção')
    axes[1].set_xlabel('X')
    axes[1].set_ylabel('Y')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()

def get_replacement_color_for_bright(point, data, radius=2.0):
    """
    Encontra a cor média de pontos próximos não brancos.
    
    Parameters:
        point: Series - Ponto atual com coordenadas e cores
        data: DataFrame - DataFrame com todos os pontos
        radius: float - Raio de busca para pontos próximos
    """
    x, y, z = point['x'], point['y'], point['z']
    # Filtrar pontos próximos
    nearby_points = data[
        (~data['is_bright']) &  # Apenas pontos não brancos
        (np.abs(data['x'] - x) <= radius) & 
        (np.abs(data['y'] - y) <= radius) &
        (np.abs(data['z'] - z) <= radius)
    ]
    if nearby_points.empty:
        return None
    # Calcular a média de R, G, B dos pontos próximos
    avg_r = nearby_points['r'].mean()
    avg_g = nearby_points['g'].mean()
    avg_b = nearby_points['b'].mean()
    return int(avg_r), int(avg_g), int(avg_b)

def correct_bright_colors(data, bright_threshold=240, radius=2.0):
    """
    Corrige cores muito claras (brancas) substituindo pela média das cores próximas.
    
    Parameters:
        data: DataFrame - DataFrame com colunas r, g, b, x, y, z
        bright_threshold: int - Valor mínimo para considerar uma cor como branca
        radius: float - Raio de busca para pontos próximos
    """
    # Identifica cores muito claras (média dos canais acima do threshold)
    data['is_bright'] = data[['r', 'g', 'b']].mean(axis=1) > bright_threshold
    
    # Corrige cores muito claras
    for index, row in data[data['is_bright']].iterrows():
        replacement_color = get_replacement_color_for_bright(row, data, radius)
        if replacement_color:
            data.loc[index, ['r', 'g', 'b']] = replacement_color
    
    return data

def correct_colors(data, dark_threshold=50, bright_threshold=240, radius=2.0):
    """
    Aplica correção tanto para cores escuras quanto para cores claras.
    
    Parameters:
        data: DataFrame - DataFrame com colunas r, g, b, x, y, z
        dark_threshold: int - Valor máximo para considerar uma cor como escura
        bright_threshold: int - Valor mínimo para considerar uma cor como branca
        radius: float - Raio de busca para pontos próximos
    """
    # Primeiro corrige as cores escuras
    data = correct_dark_colors(data, dark_threshold, radius)
    # Depois corrige as cores claras
    data = correct_bright_colors(data, bright_threshold, radius)
    return data
