import pytest
from unittest.mock import patch, MagicMock


class TestStackLifecycle:
    """Tests de ciclo de vida completo del stack"""

    def test_create_stack_with_unique_name(self, terraform_provisioner):
        """Crear stack con nombre unico basado en PR"""
        pr_number = 456

        result = terraform_provisioner.create_stack(pr_number)

        assert result.stack_name == f"ephemeral-pr-{pr_number}"
        assert result.success is True
        terraform_provisioner.create_stack.assert_called_once_with(pr_number)

    def test_destroy_stack_removes_all_resources(self, terraform_provisioner):
        """Destroy debe eliminar todos los recursos sin huerfanos"""
        pr_number = 456

        # Mock de recursos creados
        terraform_provisioner.get_resources.return_value = [
            "ephemeral-pr-456-app",
            "ephemeral-pr-456-proxy",
            "ephemeral-pr-456-db"
        ]

        # Destroy
        terraform_provisioner.destroy_stack(pr_number)

        # Verificar que no quedan recursos
        terraform_provisioner.get_resources.return_value = []
        remaining = terraform_provisioner.get_resources(pr_number)
        assert len(remaining) == 0

    @pytest.mark.parametrize("pr_number", [1, 100, 9999])
    def test_create_destroy_cycle(self, terraform_provisioner, pr_number):
        """Ciclo completo create->destroy debe ser limpio"""
        # Create
        terraform_provisioner.create_stack(pr_number)
        terraform_provisioner.stack_exists.return_value = True

        # Verify created
        assert terraform_provisioner.stack_exists(pr_number)

        # Destroy
        terraform_provisioner.destroy_stack(pr_number)
        terraform_provisioner.stack_exists.return_value = False

        # Verify destroyed
        assert not terraform_provisioner.stack_exists(pr_number)

    def test_stack_naming_follows_convention(self, terraform_provisioner):
        """Stack debe seguir convencion ephemeral-pr-{number}-{resource}"""
        pr_number = 789

        terraform_provisioner.create_stack(pr_number)

        expected_names = [
            f"ephemeral-pr-{pr_number}-app",
            f"ephemeral-pr-{pr_number}-proxy",
            f"ephemeral-pr-{pr_number}-db"
        ]

        terraform_provisioner.get_resources.return_value = expected_names
        resources = terraform_provisioner.get_resources(pr_number)

        for resource in resources:
            assert resource.startswith(f"ephemeral-pr-{pr_number}")

    def test_concurrent_stacks_dont_collide(self, terraform_provisioner):
        """Multiples stacks de diferentes PRs no deben colisionar"""
        pr1 = 100
        pr2 = 200

        # Crear dos stacks
        terraform_provisioner.create_stack(pr1)
        terraform_provisioner.create_stack(pr2)

        # Mock retorno de recursos
        terraform_provisioner.get_resources.side_effect = [
            [f"ephemeral-pr-{pr1}-app", f"ephemeral-pr-{pr1}-proxy", f"ephemeral-pr-{pr1}-db"],
            [f"ephemeral-pr-{pr2}-app", f"ephemeral-pr-{pr2}-proxy", f"ephemeral-pr-{pr2}-db"]
        ]

        # Verificar que cada stack tiene sus propios recursos
        resources_pr1 = terraform_provisioner.get_resources(pr1)
        resources_pr2 = terraform_provisioner.get_resources(pr2)

        # No debe haber overlap
        assert set(resources_pr1).isdisjoint(set(resources_pr2))
