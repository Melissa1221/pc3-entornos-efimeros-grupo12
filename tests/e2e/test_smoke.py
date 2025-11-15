
import os
import pytest
import requests
from typing import Dict


@pytest.fixture(scope="module")
def stack_urls() -> Dict[str, str]:
    """Obtiene URLs del stack desde variables de entorno o usa defaults basados en PR_NUMBER."""
    pr_number = os.getenv("PR_NUMBER", "123")

    # Puertos dinámicos: 80XX proxy, 81XX app (XX = PR % 100)
    proxy_port = 8000 + (int(pr_number) % 100)
    app_port = 8100 + (int(pr_number) % 100)

    app_url = os.getenv("STACK_APP_URL", f"http://localhost:{app_port}")
    proxy_url = os.getenv("STACK_PROXY_URL", f"http://localhost:{proxy_port}")

    return {
        "app": app_url,
        "proxy": proxy_url,
        "pr_number": pr_number
    }


@pytest.fixture(scope="module")
def verify_stack_deployed(stack_urls):
    """Verifica que el stack esté desplegado o salta los tests."""
    try:
        requests.get(stack_urls["proxy"], timeout=2, allow_redirects=False)
        return True
    except requests.exceptions.RequestException:
        pr_num = stack_urls['pr_number']
        pytest.skip(f"Stack no desplegado. Ejecuta 'terraform apply' para PR #{pr_num}")


class TestSmokeE2E:
    """Tests e2e que validan el stack completo desplegado."""

    def test_app_responds_200(self, stack_urls, verify_stack_deployed):
        """Verifica que la aplicación responde con HTTP 200 OK."""
        app_url = stack_urls["app"]
        response = requests.get(app_url, timeout=5)

        assert response.status_code == 200, (
            f"App no respondió con 200 OK. Status: {response.status_code}, URL: {app_url}"
        )
        assert len(response.text) > 0, "App respondió con body vacío"

        print(f"App OK en {app_url} - Status: {response.status_code}, Bytes: {len(response.text)}")

    def test_proxy_forwards_to_app(self, stack_urls, verify_stack_deployed):
        """Confirma que el proxy redirige correctamente al app."""
        proxy_url = stack_urls["proxy"]
        response = requests.get(proxy_url, timeout=5, allow_redirects=True)

        assert response.status_code == 200, (
            f"Proxy no redirigió correctamente. Status: {response.status_code}, URL: {proxy_url}"
        )
        assert len(response.text) > 0, "Proxy respondió con body vacío"

        print(f"Proxy OK en {proxy_url} - Final URL: {response.url}")

    @pytest.mark.parametrize("endpoint", ["/health", "/api/status"])
    def test_health_endpoints(self, stack_urls, verify_stack_deployed, endpoint):
        """Valida que los endpoints de salud están disponibles y responden correctamente."""
        proxy_url = stack_urls["proxy"]
        full_url = f"{proxy_url}{endpoint}"
        response = requests.get(full_url, timeout=5)

        assert response.status_code == 200, (
            f"Health endpoint {endpoint} no respondió con 200. "
            f"Status: {response.status_code}, URL: {full_url}"
        )

        content_type = response.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                health_data = response.json()
                assert isinstance(health_data, dict), "Health data debe ser un objeto JSON"
                status = health_data.get('status', 'unknown')
                print(f"Health {endpoint} OK - JSON válido, status: {status}")
            except ValueError:
                pytest.fail(f"Endpoint {endpoint} declaró JSON pero no es parseable")
        else:
            assert len(response.text) > 0, f"Health endpoint {endpoint} respondió vacío"
            print(f"Health {endpoint} OK - Texto plano")

        print(f"  URL: {full_url}, Status: {response.status_code}, Type: {content_type}")
