"""Clase base TerraformProvisioner para abstracción de provisioning."""


class TerraformProvisioner:
    """Provisioner de Terraform siguiendo el patrón DIP."""

    def __init__(self, terraform_dir="infra/terraform/stacks/pr-preview"):
        self.terraform_dir = terraform_dir

    def apply(self, pr_number):
        """Aplica configuración de Terraform."""
        pass

    def destroy(self, pr_number):
        """Destruye stack de Terraform."""
        pass

    def get_state(self, pr_number):
        """Obtiene estado del stack."""
        pass

    def plan(self, pr_number):
        """Genera plan de Terraform."""
        pass
