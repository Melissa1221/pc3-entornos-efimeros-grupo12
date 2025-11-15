#!/usr/bin/env python3
"""
Tests de cleanup para verificar 0 recursos huérfanos.
Verifica que después de destroy no queden contenedores, volúmenes o redes.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch
from typing import List, Dict


class DockerManager:
    """Gestor de operaciones Docker para tests de cleanup."""

    @staticmethod
    def get_containers_by_pr(pr_number: int) -> List[str]:
        """Obtiene contenedores asociados a un PR específico."""
        try:
            cmd = [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"label=pr_number={pr_number}",
                "--format",
                "{{.Names}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            containers = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            return [c for c in containers if c]  # Filtrar strings vacíos
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_volumes_by_pr(pr_number: int) -> List[str]:
        """Obtiene volúmenes asociados a un PR específico."""
        try:
            cmd = [
                "docker",
                "volume",
                "ls",
                "--filter",
                f"name=ephemeral-pr-{pr_number}",
                "--format",
                "{{.Name}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            volumes = result.stdout.strip().split("\n") if result.stdout.strip() else []
            return [v for v in volumes if v]  # Filtrar strings vacíos
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_networks_by_pr(pr_number: int) -> List[str]:
        """Obtiene redes asociadas a un PR específico."""
        try:
            cmd = [
                "docker",
                "network",
                "ls",
                "--filter",
                f"name=ephemeral-pr-{pr_number}",
                "--format",
                "{{.Name}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            networks = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            return [
                n
                for n in networks
                if n and n != "bridge" and n != "host" and n != "none"
            ]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def cleanup_orphaned_resources(pr_number: int) -> Dict[str, int]:
        """Limpia recursos huérfanos manualmente y retorna conteo."""
        cleaned = {"containers": 0, "volumes": 0, "networks": 0}

        # Limpiar contenedores
        containers = DockerManager.get_containers_by_pr(pr_number)
        for container in containers:
            try:
                subprocess.run(["docker", "rm", "-f", container], capture_output=True)
                cleaned["containers"] += 1
            except subprocess.CalledProcessError:
                pass

        # Limpiar volúmenes
        volumes = DockerManager.get_volumes_by_pr(pr_number)
        for volume in volumes:
            try:
                subprocess.run(["docker", "volume", "rm", volume], capture_output=True)
                cleaned["volumes"] += 1
            except subprocess.CalledProcessError:
                pass

        # Limpiar redes
        networks = DockerManager.get_networks_by_pr(pr_number)
        for network in networks:
            try:
                subprocess.run(
                    ["docker", "network", "rm", network], capture_output=True
                )
                cleaned["networks"] += 1
            except subprocess.CalledProcessError:
                pass

        return cleaned


class TerraformCleanupValidator:
    """Validador de limpieza completa de Terraform."""

    @staticmethod
    def verify_state_empty(terraform_dir: str) -> bool:
        """Verifica que el state de Terraform esté vacío."""
        try:
            cmd = ["terraform", "state", "list"]
            result = subprocess.run(
                cmd, cwd=terraform_dir, capture_output=True, text=True
            )
            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_resource_count(terraform_dir: str) -> int:
        """Obtiene el número de recursos en el state."""
        try:
            cmd = ["terraform", "state", "list"]
            result = subprocess.run(
                cmd, cwd=terraform_dir, capture_output=True, text=True
            )
            resources = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            return len([r for r in resources if r])
        except subprocess.CalledProcessError:
            return -1  # Error al obtener estado


@pytest.mark.parametrize(
    "pr_number,expected_valid",
    [
        (1, True),  # PR normal
        (99, True),  # PR doble dígito
        (1000, True),  # PR grande
        (0, False),  # PR inválido (0 no existe)
        (-1, False),  # PR negativo
        (None, False),  # PR None
        ("abc", False),  # PR no numérico
        (99999, True),  # PR muy grande (edge case)
    ],
)
def test_cleanup_validation_parameters(pr_number, expected_valid):
    """Test de validación de parámetros para cleanup."""
    docker_manager = DockerManager()

    if expected_valid and isinstance(pr_number, int) and pr_number > 0:
        # Los parámetros válidos no deben lanzar excepción
        containers = docker_manager.get_containers_by_pr(pr_number)
        assert isinstance(containers, list)

        volumes = docker_manager.get_volumes_by_pr(pr_number)
        assert isinstance(volumes, list)

        networks = docker_manager.get_networks_by_pr(pr_number)
        assert isinstance(networks, list)
    else:
        # Los parámetros inválidos deben ser manejados correctamente
        if not isinstance(pr_number, int) or pr_number <= 0:
            # Estos casos deberían retornar listas vacías o manejar el error
            if isinstance(pr_number, int) and pr_number <= 0:
                containers = docker_manager.get_containers_by_pr(pr_number)
                assert containers == []


class TestCleanupOperations:
    """Tests para operaciones de cleanup y verificación de recursos huérfanos."""

    def test_docker_manager_get_containers_empty(self):
        """Test que DockerManager retorna lista vacía cuando no hay contenedores."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            containers = DockerManager.get_containers_by_pr(123)
            assert containers == []

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "docker" in call_args
            assert "ps" in call_args
            assert "label=pr_number=123" in call_args

    def test_docker_manager_get_containers_with_results(self):
        """Test que DockerManager retorna contenedores encontrados."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = (
                "ephemeral-pr-123-app\nephemeral-pr-123-proxy\nephemeral-pr-123-db\n"
            )
            mock_run.return_value.returncode = 0

            containers = DockerManager.get_containers_by_pr(123)
            expected = [
                "ephemeral-pr-123-app",
                "ephemeral-pr-123-proxy",
                "ephemeral-pr-123-db",
            ]
            assert containers == expected

    def test_docker_manager_get_volumes_empty(self):
        """Test que DockerManager retorna lista vacía cuando no hay volúmenes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            volumes = DockerManager.get_volumes_by_pr(123)
            assert volumes == []

    def test_docker_manager_get_volumes_with_results(self):
        """Test que DockerManager retorna volúmenes encontrados."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "ephemeral-pr-123-db-data\n"
            mock_run.return_value.returncode = 0

            volumes = DockerManager.get_volumes_by_pr(123)
            assert volumes == ["ephemeral-pr-123-db-data"]

    def test_docker_manager_cleanup_orphaned_resources(self):
        """Test que cleanup_orphaned_resources limpia correctamente."""
        with patch("subprocess.run") as mock_run:
            # Mock para get_containers_by_pr
            with patch.object(
                DockerManager, "get_containers_by_pr", return_value=["container1"]
            ):
                with patch.object(
                    DockerManager, "get_volumes_by_pr", return_value=["volume1"]
                ):
                    with patch.object(
                        DockerManager, "get_networks_by_pr", return_value=["network1"]
                    ):
                        mock_run.return_value.returncode = 0

                        result = DockerManager.cleanup_orphaned_resources(123)

                        assert result["containers"] == 1
                        assert result["volumes"] == 1
                        assert result["networks"] == 1

                        # Verificar que se llamaron los comandos de limpieza
                        assert (
                            mock_run.call_count == 3
                        )  # rm container, rm volume, rm network

    def test_terraform_validator_verify_state_empty(self):
        """Test que verify_state_empty detecta state vacío correctamente."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            result = TerraformCleanupValidator.verify_state_empty("/fake/dir")
            assert result is True

            # Verificar comando correcto
            call_args = mock_run.call_args[0][0]
            assert call_args == ["terraform", "state", "list"]

    def test_terraform_validator_verify_state_not_empty(self):
        """Test que verify_state_empty detecta state con recursos."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = (
                "docker_container.app\ndocker_container.proxy\n"
            )
            mock_run.return_value.returncode = 0

            result = TerraformCleanupValidator.verify_state_empty("/fake/dir")
            assert result is False

    def test_terraform_validator_get_resource_count(self):
        """Test que get_resource_count cuenta recursos correctamente."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = "resource1\nresource2\nresource3\n"
            mock_run.return_value.returncode = 0

            count = TerraformCleanupValidator.get_resource_count("/fake/dir")
            assert count == 3

    def test_terraform_validator_get_resource_count_empty(self):
        """Test que get_resource_count retorna 0 para state vacío."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            count = TerraformCleanupValidator.get_resource_count("/fake/dir")
            assert count == 0

    def test_terraform_validator_error_handling(self):
        """Test que los validadores manejan errores correctamente."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "terraform")

            # verify_state_empty debe retornar False en caso de error
            result = TerraformCleanupValidator.verify_state_empty("/fake/dir")
            assert result is False

            # get_resource_count debe retornar -1 en caso de error
            count = TerraformCleanupValidator.get_resource_count("/fake/dir")
            assert count == -1


class TestCleanupIdempotency:
    """Tests de idempotencia para operaciones de cleanup."""

    def test_cleanup_idempotency_docker(self):
        """Test que cleanup de Docker es idempotente."""
        with patch.object(DockerManager, "get_containers_by_pr", return_value=[]):
            with patch.object(DockerManager, "get_volumes_by_pr", return_value=[]):
                with patch.object(DockerManager, "get_networks_by_pr", return_value=[]):

                    # Primera ejecución
                    result1 = DockerManager.cleanup_orphaned_resources(123)

                    # Segunda ejecución (idempotente)
                    result2 = DockerManager.cleanup_orphaned_resources(123)

                    # Ambos resultados deben ser iguales (0 recursos limpiados)
                    assert result1 == result2
                    assert result1["containers"] == 0
                    assert result1["volumes"] == 0
                    assert result1["networks"] == 0

    def test_terraform_state_idempotency(self):
        """Test que verificación de state de Terraform es idempotente."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            # Primera verificación
            result1 = TerraformCleanupValidator.verify_state_empty("/fake/dir")

            # Segunda verificación (idempotente)
            result2 = TerraformCleanupValidator.verify_state_empty("/fake/dir")

            assert result1 and result2


class TestCleanupIntegration:
    """Tests de integración para flujo completo de cleanup."""

    def test_full_cleanup_verification_flow(self):
        """Test del flujo completo de verificación de cleanup."""
        pr_number = 123
        terraform_dir = "/fake/terraform/dir"

        with patch("subprocess.run") as mock_run:
            # Mock para comandos docker (sin recursos)
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            # Verificar que no hay recursos Docker
            containers = DockerManager.get_containers_by_pr(pr_number)
            volumes = DockerManager.get_volumes_by_pr(pr_number)
            networks = DockerManager.get_networks_by_pr(pr_number)

            assert containers == []
            assert volumes == []
            assert networks == []

            # Verificar que state de Terraform está vacío
            is_empty = TerraformCleanupValidator.verify_state_empty(terraform_dir)
            resource_count = TerraformCleanupValidator.get_resource_count(terraform_dir)

            assert is_empty
            assert resource_count == 0

            # Verificar que cleanup es exitoso (0 recursos huérfanos)
            cleanup_result = DockerManager.cleanup_orphaned_resources(pr_number)
            assert sum(cleanup_result.values()) == 0

    def test_cleanup_with_orphaned_resources(self):
        """Test de cleanup cuando hay recursos huérfanos."""
        pr_number = 456

        # Simular recursos huérfanos
        with patch.object(
            DockerManager, "get_containers_by_pr", return_value=["orphan-container"]
        ):
            with patch.object(
                DockerManager, "get_volumes_by_pr", return_value=["orphan-volume"]
            ):
                with patch.object(
                    DockerManager, "get_networks_by_pr", return_value=["orphan-network"]
                ):
                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value.returncode = 0

                        # Ejecutar cleanup
                        result = DockerManager.cleanup_orphaned_resources(pr_number)

                        # Verificar que se limpiaron los recursos
                        assert result["containers"] == 1
                        assert result["volumes"] == 1
                        assert result["networks"] == 1

                        # Verificar que se ejecutaron los comandos de limpieza
                        assert mock_run.call_count == 3

    def test_partial_cleanup_failure(self):
        """Test de manejo de fallos parciales en cleanup."""
        pr_number = 789

        with patch.object(
            DockerManager, "get_containers_by_pr", return_value=["container1"]
        ):
            with patch.object(
                DockerManager, "get_volumes_by_pr", return_value=["volume1"]
            ):
                with patch.object(
                    DockerManager, "get_networks_by_pr", return_value=["network1"]
                ):
                    with patch("subprocess.run") as mock_run:
                        # Simular fallo en cleanup de volúmenes
                        def side_effect(cmd, **kwargs):
                            if "volume" in cmd:
                                raise subprocess.CalledProcessError(1, cmd)
                            mock_result = Mock()
                            mock_result.returncode = 0
                            return mock_result

                        mock_run.side_effect = side_effect

                        result = DockerManager.cleanup_orphaned_resources(pr_number)

                        # Containers y networks se limpiaron, volumes falló
                        assert result["containers"] == 1
                        assert result["volumes"] == 0  # Falló la limpieza
                        assert result["networks"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
