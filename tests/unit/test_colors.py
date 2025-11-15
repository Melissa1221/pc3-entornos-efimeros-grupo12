"""
Tests para el módulo de colores
"""

import pytest
from src.colors import obtener_color_hex, es_color_valido


class TestColores:
    """Tests del módulo de colores"""

    @pytest.mark.parametrize("nombre,hex_esperado", [
        ("rojo", "#FF0000"),
        ("verde", "#00FF00"),
        ("azul", "#0000FF"),
        ("amarillo", "#FFFF00"),
        ("ROJO", "#FF0000"),  # Case insensitive
    ])
    def test_obtener_color_hex_valido(self, nombre, hex_esperado):
        """Obtener código hex de colores válidos"""
        assert obtener_color_hex(nombre) == hex_esperado

    def test_obtener_color_hex_invalido(self):
        """Obtener color inválido debe lanzar ValueError"""
        with pytest.raises(ValueError, match="Color 'morado' no disponible"):
            obtener_color_hex("morado")

    @pytest.mark.parametrize("nombre,es_valido", [
        ("rojo", True),
        ("verde", True),
        ("morado", False),
        ("AZUL", True),
        ("", False),
    ])
    def test_es_color_valido(self, nombre, es_valido):
        """Verificar si un color es válido"""
        assert es_color_valido(nombre) == es_valido
