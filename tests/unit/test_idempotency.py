import pytest
from unittest.mock import patch, call


def test_terraform_apply_idempotent(terraform_provisioner):
    """Aplicar Terraform 2 veces debe dar mismo resultado"""
    pr_number = 123

    # Primera aplicación
    result1 = terraform_provisioner.apply(pr_number)

    # Segunda aplicación (debe ser idempotente)
    result2 = terraform_provisioner.apply(pr_number)

    assert result1 == result2
    # Verificar con call_args_list
    assert terraform_provisioner.apply.call_count == 2


@pytest.mark.parametrize("apply_count", [1, 2, 3])
def test_multiple_applies_same_state(terraform_provisioner, apply_count):
    """Múltiples applies deben mantener mismo estado"""
    # Implementar test
    pass


def test_terraform_with_config_override():
    """Test usando patch.dict para sobrescribir configuración"""
    from src.provisioner import TerraformProvisioner

    config = {
        "TERRAFORM_DIR": "custom/path",
        "AUTO_APPROVE": "true"
    }

    with patch.dict('os.environ', config):
        provisioner = TerraformProvisioner()
        result = provisioner.apply(123)
        assert result is not None
