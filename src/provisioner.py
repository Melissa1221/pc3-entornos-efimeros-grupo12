"""Clase base TerraformProvisioner para abstracción de provisioning."""


class TerraformProvisioner:
    """Provisioner de Terraform siguiendo el patrón DIP."""

    def __init__(self, terraform_dir="infra/terraform/stacks/pr-preview"):
        self.terraform_dir = terraform_dir

    def apply(self, pr_number):
        """Aplica configuración de Terraform."""
        return {"status": "success", "pr_number": pr_number}

    def destroy(self, pr_number):
        """Destruye stack de Terraform."""
        pass

    def get_state(self, pr_number):
        """Obtiene estado del stack."""
        pass

    def plan(self, pr_number):
        """Genera plan de Terraform."""
        pass

    def create_stack(self, pr_number):
        """Crea stack de Terraform."""
        return self.apply(pr_number)

    def get_resources(self, pr_number):
        """Obtiene recursos del stack."""
        return []

    def destroy_stack(self, pr_number):
        """Destruye stack específico."""
        return self.destroy(pr_number)

    def stack_exists(self, pr_number):
        """Verifica si stack existe."""
        return False
