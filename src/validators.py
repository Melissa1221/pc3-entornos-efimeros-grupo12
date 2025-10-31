"""Funciones de validación para el proyecto de entornos efímeros."""


def validate_pr_number(pr_number):
    """
    Valida que el número de PR sea válido para naming de stack.
    
    Args:
        pr_number: Número de Pull Request a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if pr_number is None:
        return False
    
    if not isinstance(pr_number, int):
        return False
    
    if pr_number <= 0:
        return False
    
    return True


def generate_stack_name(pr_number):
    """
    Genera nombre de stack basado en PR number.
    
    Args:
        pr_number: Número de Pull Request
        
    Returns:
        str: Nombre del stack si PR es válido, None en caso contrario
    """
    if not validate_pr_number(pr_number):
        return None
    
    return f"ephemeral-pr-{pr_number}"