"""Basic regression tests for the BaakBook Flask entry point."""

import app as app_module


app_module.app.config.update(TESTING=True)
client = app_module.app.test_client()


def test_storefront_is_served() -> None:
    """The root route returns the customer storefront."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Baak" in response.data


def test_products_api_returns_json() -> None:
    """The public product endpoint remains available."""
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.is_json
    assert isinstance(response.get_json(), list)


def test_admin_is_denied_when_token_is_not_configured() -> None:
    """A missing administrator secret fails closed."""
    original_token = app_module.ADMIN_TOKEN
    try:
        app_module.ADMIN_TOKEN = ""
        response = client.get("/api/admin/products")
        assert response.status_code == 401
    finally:
        app_module.ADMIN_TOKEN = original_token
