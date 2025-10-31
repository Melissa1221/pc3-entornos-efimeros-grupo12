import pytest
from src.validators import validate_pr_number, generate_stack_name


@pytest.mark.parametrize("pr_number,expected_valid", [
    (1, True),           # PR normal
    (99, True),          # PR doble dígito
    (1000, True),        # PR grande
    (0, False),          # PR inválido
    (-1, False),         # PR negativo
    (None, False),       # PR None
    ("abc", False),      # PR no numérico
    (99999, True),       # PR muy grande
])
def test_stack_naming_validation(pr_number, expected_valid):
    """Valida nombres de stack según PR number"""
    result = validate_pr_number(pr_number)
    assert result == expected_valid


@pytest.mark.parametrize("pr_number,expected_name", [
    (1, "ephemeral-pr-1"),
    (123, "ephemeral-pr-123"),
    (9999, "ephemeral-pr-9999"),
    (0, None),           # PR inválido
    (-1, None),          # PR negativo
    (None, None),        # PR None
    ("abc", None),       # PR no numérico
])
def test_generate_stack_name(pr_number, expected_name):
    """Verifica generación correcta de nombres de stack"""
    result = generate_stack_name(pr_number)
    assert result == expected_name


def test_stack_name_uniqueness():
    """Verifica que diferentes PRs generan nombres únicos"""
    name1 = generate_stack_name(123)
    name2 = generate_stack_name(456)
    name3 = generate_stack_name(123)  # Mismo PR
    
    assert name1 != name2  # Diferentes PRs = nombres diferentes
    assert name1 == name3  # Mismo PR = mismo nombre