"""
Módulo simple de colores para demo de PR
"""

COLORES_DISPONIBLES = {
    "rojo": "#FF0000",
    "verde": "#00FF00",
    "azul": "#0000FF",
    "amarillo": "#FFFF00",
}


def obtener_color_hex(nombre_color: str) -> str:
    """
    Obtiene el código hexadecimal de un color.

    Args:
        nombre_color: Nombre del color en español

    Returns:
        Código hexadecimal del color

    Raises:
        ValueError: Si el color no existe
    """
    color_lower = nombre_color.lower()
    if color_lower not in COLORES_DISPONIBLES:
        raise ValueError(f"Color '{nombre_color}' no disponible")

    return COLORES_DISPONIBLES[color_lower]


def es_color_valido(nombre_color: str) -> bool:
    """
    Verifica si un color está disponible.

    Args:
        nombre_color: Nombre del color a verificar

    Returns:
        True si el color existe, False en caso contrario
    """
    return nombre_color.lower() in COLORES_DISPONIBLES
