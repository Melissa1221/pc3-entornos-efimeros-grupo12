#!/usr/bin/env python3
"""
Tests de verificación de cleanup para recursos huérfanos.
"""

import pytest
import subprocess
from unittest.mock import Mock, patch, create_autospec
from typing import List, Dict


class CleanupVerifier:
    """Verificador de limpieza de recursos huérfanos."""

    @staticmethod
    def get_orphaned_containers(pr_number: int) -> List[str]:
        """Obtiene contenedores huérfanos para un PR."""
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
            return [c for c in containers if c]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def get_orphaned_volumes(pr_number: int) -> List[str]:
        """Obtiene volúmenes huérfanos para un PR."""
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
            return [v for v in volumes if v]
        except subprocess.CalledProcessError:
            return []

    @staticmethod
    def verify_terraform_state_empty(terraform_dir: str) -> bool:
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
    def cleanup_orphaned_resources(pr_number: int) -> Dict[str, int]:
        """Limpia recursos huérfanos y retorna conteo."""
        cleaned = {"containers": 0, "volumes": 0}

        containers = CleanupVerifier.get_orphaned_containers(pr_number)
        for container in containers:
            try:
                subprocess.run(["docker", "rm", "-f", container], capture_output=True)
                cleaned["containers"] += 1
            except subprocess.CalledProcessError:
                pass

        volumes = CleanupVerifier.get_orphaned_volumes(pr_number)
        for volume in volumes:
            try:
                subprocess.run(["docker", "volume", "rm", volume], capture_output=True)
                cleaned["volumes"] += 1
            except subprocess.CalledProcessError:
                pass

        return cleaned


@pytest.mark.parametrize(
    "pr_number,expected_valid",
    [
        (1, True),
        (99, True),
        (1000, True),
        (0, False),
        (-1, False),
        (None, False),
        ("abc", False),
        (99999, True),
    ],
)
def test_cleanup_validation_parameters(pr_number, expected_valid):
    """Test de validación de parámetros para cleanup."""
    verifier = CleanupVerifier()

    if expected_valid and isinstance(pr_number, int) and pr_number > 0:
        containers = verifier.get_orphaned_containers(pr_number)
        assert isinstance(containers, list)

        volumes = verifier.get_orphaned_volumes(pr_number)
        assert isinstance(volumes, list)
    else:
        if isinstance(pr_number, int) and pr_number <= 0:
            containers = verifier.get_orphaned_containers(pr_number)
            assert containers == []


class TestCleanupOperations:
    """Tests para operaciones de cleanup."""

    def test_get_orphaned_containers_empty(self):
        """Test que retorna lista vacía cuando no hay contenedores."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            containers = CleanupVerifier.get_orphaned_containers(123)
            assert containers == []

    def test_get_orphaned_containers_with_results(self):
        """Test que retorna contenedores encontrados."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = (
                "ephemeral-pr-123-app\nephemeral-pr-123-proxy\n"
            )
            mock_run.return_value.returncode = 0

            containers = CleanupVerifier.get_orphaned_containers(123)
            expected = ["ephemeral-pr-123-app", "ephemeral-pr-123-proxy"]
            assert containers == expected

    def test_get_orphaned_volumes_empty(self):
        """Test que retorna lista vacía cuando no hay volúmenes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            volumes = CleanupVerifier.get_orphaned_volumes(123)
            assert volumes == []

    def test_verify_terraform_state_empty(self):
        """Test que verifica state vacío correctamente."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            result = CleanupVerifier.verify_terraform_state_empty("/fake/dir")
            assert result is True

    def test_verify_terraform_state_not_empty(self):
        """Test que detecta state con recursos."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = (
                "docker_container.app\ndocker_container.proxy\n"
            )
            mock_run.return_value.returncode = 0

            result = CleanupVerifier.verify_terraform_state_empty("/fake/dir")
            assert result is False

    def test_cleanup_orphaned_resources(self):
        """Test que cleanup limpia correctamente."""
        with patch("subprocess.run") as mock_run:
            with patch.object(
                CleanupVerifier, "get_orphaned_containers", return_value=["container1"]
            ):
                with patch.object(
                    CleanupVerifier, "get_orphaned_volumes", return_value=["volume1"]
                ):
                    mock_run.return_value.returncode = 0

                    result = CleanupVerifier.cleanup_orphaned_resources(123)

                    assert result["containers"] == 1
                    assert result["volumes"] == 1


class TestCleanupIdempotency:
    """Tests de idempotencia para operaciones de cleanup."""

    def test_cleanup_idempotency(self):
        """Test que cleanup es idempotente."""
        with patch.object(CleanupVerifier, "get_orphaned_containers", return_value=[]):
            with patch.object(CleanupVerifier, "get_orphaned_volumes", return_value=[]):

                result1 = CleanupVerifier.cleanup_orphaned_resources(123)
                result2 = CleanupVerifier.cleanup_orphaned_resources(123)

                assert result1 == result2
                assert result1["containers"] == 0
                assert result1["volumes"] == 0

    def test_terraform_state_idempotency(self):
        """Test que verificación de state es idempotente."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            result1 = CleanupVerifier.verify_terraform_state_empty("/fake/dir")
            result2 = CleanupVerifier.verify_terraform_state_empty("/fake/dir")

            assert result1 == result2 == True


class TestCleanupIntegration:
    """Tests de integración para flujo completo de cleanup."""

    def test_full_cleanup_verification_flow(self):
        """Test del flujo completo de verificación de cleanup."""
        pr_number = 123
        terraform_dir = "/fake/terraform/dir"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            containers = CleanupVerifier.get_orphaned_containers(pr_number)
            volumes = CleanupVerifier.get_orphaned_volumes(pr_number)

            assert containers == []
            assert volumes == []

            is_empty = CleanupVerifier.verify_terraform_state_empty(terraform_dir)
            assert is_empty is True

            cleanup_result = CleanupVerifier.cleanup_orphaned_resources(pr_number)
            assert sum(cleanup_result.values()) == 0

    def test_cleanup_with_orphaned_resources(self):
        """Test de cleanup cuando hay recursos huérfanos."""
        pr_number = 456

        with patch.object(
            CleanupVerifier,
            "get_orphaned_containers",
            return_value=["orphan-container"],
        ):
            with patch.object(
                CleanupVerifier, "get_orphaned_volumes", return_value=["orphan-volume"]
            ):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.returncode = 0

                    result = CleanupVerifier.cleanup_orphaned_resources(pr_number)

                    assert result["containers"] == 1
                    assert result["volumes"] == 1

    def test_partial_cleanup_failure(self):
        """Test de manejo de fallos parciales en cleanup."""
        pr_number = 789

        with patch.object(
            CleanupVerifier, "get_orphaned_containers", return_value=["container1"]
        ):
            with patch.object(
                CleanupVerifier, "get_orphaned_volumes", return_value=["volume1"]
            ):
                with patch("subprocess.run") as mock_run:

                    def side_effect(cmd, **kwargs):
                        if "volume" in cmd:
                            raise subprocess.CalledProcessError(1, cmd)
                        mock_result = Mock()
                        mock_result.returncode = 0
                        return mock_result

                    mock_run.side_effect = side_effect

                    result = CleanupVerifier.cleanup_orphaned_resources(pr_number)

                    assert result["containers"] == 1
                    assert result["volumes"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
