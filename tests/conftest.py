import pytest
from unittest.mock import create_autospec


@pytest.fixture(scope="session")
def terraform_provisioner():
    """Mock del provisioner de Terraform con autospec"""
    from src.provisioner import TerraformProvisioner

    return create_autospec(TerraformProvisioner)


@pytest.fixture(scope="function")
def pr_environment(monkeypatch):
    """Fixture para configurar environment de PR"""
    monkeypatch.setenv("PR_NUMBER", "123")
    yield
    # Cleanup automático


@pytest.fixture(autouse=True, scope="function")
def cleanup_resources():
    """Fixture autouse para limpieza de recursos"""
    yield
    # Cleanup code
