import cv2
import numpy as np
from typing import Tuple, Optional


def calculate_polygon_area(points: np.ndarray) -> float:
    """
    Calcula a área de um polígono usando a fórmula da área do polígono.

    Parameters:
        points: np.ndarray - Array de pontos do polígono (coordenadas normalizadas)

    Returns:
        float - Área do polígono
    """
    # Garante que os pontos estão no formato correto
    points = points.reshape(-1, 2)

    # Fecha o polígono se necessário
    if not np.array_equal(points[0], points[-1]):
        points = np.vstack((points, points[0]))

    # Calcula a área usando a fórmula do polígono
    x = points[:, 0]
    y = points[:, 1]
    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

    return area


def adjust_mask_with_min_rect(
    segmentation_data: dict, size: tuple = (512, 512)
) -> np.ndarray:
    """
    Ajusta a máscara usando o método de retângulo mínimo (minimum area rectangle).

    Parameters:
        segmentation_data: dict - Retorno da função get_best_segmentation
        size: tuple - Dimensões da imagem (default: 512x512)

    Returns:
        np.ndarray - Array com as coordenadas normalizadas do polígono ajustado
    """
    h, w = size

    # Cria máscara binária a partir do polígono original
    original_polygon = segmentation_data["polygon"]
    mask = np.zeros((h, w), dtype=np.uint8)
    points = np.array(original_polygon * [w, h], dtype=np.int32)
    cv2.fillPoly(mask, [points], 1)

    # Encontra contornos
    mask_uint8 = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(
        mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Pega o maior contorno
    largest_contour = max(contours, key=cv2.contourArea)

    # Aplica minimum area rectangle
    rect = cv2.minAreaRect(largest_contour)
    points = cv2.boxPoints(rect)

    # Normaliza as coordenadas (0..1)
    points = points.astype(float)
    points[:, 0] /= w
    points[:, 1] /= h

    return points


def adjust_mask_with_approx_poly(
    segmentation_data: dict,
    size: tuple = (512, 512),
    epsilon_factor: float = 0.04,  # Aumentado para maior simplificação
    min_points: int = 4,  # Mínimo de pontos desejados
    max_points: int = 6,  # Máximo de pontos desejados
) -> np.ndarray:
    """
    Ajusta a máscara usando aproximação poligonal (Douglas-Peucker algorithm).
    Tenta encontrar o melhor epsilon que resulte em um polígono com número de pontos
    dentro do intervalo desejado.

    Parameters:
        segmentation_data: dict - Retorno da função get_best_segmentation
        size: tuple - Dimensões da imagem (default: 512x512)
        epsilon_factor: float - Fator inicial para controle da aproximação
        min_points: int - Número mínimo de pontos desejados
        max_points: int - Número máximo de pontos desejados

    Returns:
        np.ndarray - Array com as coordenadas normalizadas do polígono ajustado
    """
    h, w = size

    # Cria máscara binária a partir do polígono original
    original_polygon = segmentation_data["polygon"]
    mask = np.zeros((h, w), dtype=np.uint8)
    points = np.array(original_polygon * [w, h], dtype=np.int32)
    cv2.fillPoly(mask, [points], 1)

    # Encontra contornos
    mask_uint8 = mask.astype(np.uint8) * 255
    contours, _ = cv2.findContours(
        mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    # Pega o maior contorno
    largest_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(largest_contour, True)

    # Busca binária para encontrar o melhor epsilon
    epsilon_min = epsilon_factor * 0.5
    epsilon_max = epsilon_factor * 2.0
    best_approx = None
    best_points = 0

    for _ in range(10):  # Máximo de 10 tentativas
        epsilon = (epsilon_min + epsilon_max) / 2
        current_epsilon = epsilon * perimeter
        approx = cv2.approxPolyDP(largest_contour, current_epsilon, True)
        num_points = len(approx)

        if num_points >= min_points and num_points <= max_points:
            best_approx = approx
            break
        elif num_points > max_points:
            epsilon_min = epsilon
        else:
            epsilon_max = epsilon

        # Guarda a melhor aproximação até agora
        if best_approx is None or abs(
            num_points - (min_points + max_points) / 2
        ) < abs(best_points - (min_points + max_points) / 2):
            best_approx = approx
            best_points = num_points

    if best_approx is None:
        return None

    # Normaliza as coordenadas (0..1)
    points = best_approx.reshape(-1, 2).astype(float)
    points[:, 0] /= w
    points[:, 1] /= h

    print(f"Polígono ajustado com {len(points)} pontos")
    return points


def is_polygon_convex(points: np.ndarray) -> bool:
    """
    Verifica se um polígono é convexo usando o produto vetorial.

    Args:
        points: np.ndarray - Array de pontos do polígono

    Returns:
        bool - True se o polígono é convexo, False caso contrário
    """
    # Garante que os pontos estão no formato correto
    points = points.reshape(-1, 2)
    n = len(points)

    if n < 3:
        return True

    # Fecha o polígono se necessário
    if not np.array_equal(points[0], points[-1]):
        points = np.vstack((points, points[0]))

    # Calcula o produto vetorial para cada três pontos consecutivos
    sign = 0
    for i in range(len(points) - 2):
        v1 = points[i + 1] - points[i]
        v2 = points[i + 2] - points[i + 1]
        cross_product = np.cross(v1, v2)

        if sign == 0:
            sign = np.sign(cross_product)
        elif (
            sign * cross_product < 0
        ):  # Mudança de sinal indica polígono côncavo
            return False

    return True


def adjust_rectangle_area(
    points: np.ndarray, target_area_ratio: float
) -> np.ndarray:
    """
    Ajusta a área de um retângulo mantendo seu centro e proporção,
    mas alterando suas dimensões para atingir a área desejada.

    Args:
        points: np.ndarray - Pontos do retângulo (4 pontos, normalizado 0-1)
        target_area_ratio: float - Razão da área desejada (ex: 0.91 para 91% da área original)

    Returns:
        np.ndarray - Pontos do retângulo ajustado
    """
    # Calcula o centro do retângulo
    center = points.mean(axis=0)

    # Calcula o fator de escala para atingir a área desejada
    # Como área = base * altura, e queremos manter a proporção,
    # usamos a raiz quadrada da razão das áreas
    scale_factor = np.sqrt(target_area_ratio)

    # Ajusta os pontos em relação ao centro
    adjusted_points = center + (points - center) * scale_factor

    return adjusted_points


def select_best_polygon_adjustment(
    segmentation_data: dict,
    original_area: float,
    size: tuple = (512, 512),
    area_diff_threshold: float = 0.18,  # 15% de diferença
    min_points: int = 4,
    max_points: int = 6,
) -> Tuple[Optional[np.ndarray], str]:
    """
    Seleciona o melhor método de ajuste de polígono baseado na diferença de área
    e na convexidade do polígono.
    """
    # Tenta primeiro com minimum area rectangle
    min_rect_polygon = adjust_mask_with_min_rect(segmentation_data, size)
    if min_rect_polygon is None:
        return None, "none"

    # Calcula área do retângulo mínimo em pixels (normalizada)
    min_rect_area_pixels = calculate_polygon_area(min_rect_polygon)

    # Calcula área do polígono original em pixels (normalizada)
    original_polygon = segmentation_data["polygon"]
    original_area_pixels = calculate_polygon_area(original_polygon)

    # Calcula a diferença relativa entre as áreas para min_rect
    min_rect_area_difference = (
        min_rect_area_pixels - original_area_pixels
    ) / original_area_pixels

    # Se min_rect está dentro do threshold, usa ele imediatamente
    if abs(min_rect_area_difference) <= area_diff_threshold:
        print(
            f"Usando min_rect devido à diferença de área aceitável: {min_rect_area_difference:.2%}"
        )
        return min_rect_polygon, "min_rect"

    # Se min_rect não está dentro do threshold, tenta com aproximação poligonal
    approx_polygon = adjust_mask_with_approx_poly(
        segmentation_data,
        size=size,
        min_points=min_points,
        max_points=max_points,
    )

    # Se approx_poly é válido e convexo, calcula sua diferença de área
    if approx_polygon is not None and is_polygon_convex(approx_polygon):
        approx_area_pixels = calculate_polygon_area(approx_polygon)
        approx_area_difference = (
            approx_area_pixels - original_area_pixels
        ) / original_area_pixels
        print(f"Diferença de área min_rect: {min_rect_area_difference:.2%}")
        print(f"Diferença de área approx_poly: {approx_area_difference:.2%}")

        # Usa approx_poly apenas se tiver diferença significativamente menor
        if (
            abs(approx_area_difference) < abs(min_rect_area_difference) * 0.8
        ):  # 20% melhor
            print(
                "Usando approx_poly devido à diferença de área significativamente menor"
            )
            return approx_polygon, "approx_poly"

    # Se chegou aqui, ajusta o retângulo para ter a área desejada
    print(
        f"Usando min_rect ajustado (diferença original: {min_rect_area_difference:.2%})"
    )
    target_area_ratio = original_area_pixels / min_rect_area_pixels
    adjusted_rect = adjust_rectangle_area(min_rect_polygon, target_area_ratio)

    # Verifica o resultado do ajuste
    adjusted_area = calculate_polygon_area(adjusted_rect)
    final_diff = (adjusted_area - original_area_pixels) / original_area_pixels
    print(f"Diferença após ajuste: {final_diff:.2%}")

    return adjusted_rect, "adjusted_min_rect"
