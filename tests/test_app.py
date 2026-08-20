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


def test_discover_returns_explainable_recommendations() -> None:
    """The discovery quiz returns up to three stocked books with reasons."""
    response = client.post(
        "/api/discover",
        json={"goal": "growth", "pace": "quick", "mood": "change"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert 1 <= len(payload["recommendations"]) <= 3
    assert all(item["reason"] for item in payload["recommendations"])


def test_discover_rejects_incomplete_answers() -> None:
    """The discovery quiz fails clearly when an answer is missing or invalid."""
    response = client.post(
        "/api/discover",
        json={"goal": "growth", "pace": "quick", "mood": "not-a-real-option"},
    )
    assert response.status_code == 400
    assert response.get_json()["fields"] == ["mood"]


def test_admin_can_read_and_update_feature_flags(monkeypatch) -> None:
    """Feature visibility is controllable from the protected dashboard API."""
    monkeypatch.setattr(app_module, "ADMIN_TOKEN", "local-test-token")
    original = dict(app_module.settings["features"])
    monkeypatch.setattr(app_module, "save_data", lambda: None)
    try:
        headers = {"Authorization": "Bearer local-test-token"}
        response = client.get("/api/admin/settings", headers=headers)
        assert response.status_code == 200
        assert "gifts" in response.get_json()["features"]

        response = client.put(
            "/api/admin/settings",
            headers=headers,
            json={"features": {"gifts": False, "on_demand": True}},
        )
        assert response.status_code == 200
        assert response.get_json()["features"]["gifts"] is False
        assert response.get_json()["features"]["on_demand"] is True
    finally:
        app_module.settings["features"] = original


def test_admin_product_contract_supports_on_demand_metadata(monkeypatch) -> None:
    """The product admin API accepts lead time and on-demand availability."""
    monkeypatch.setattr(app_module, "ADMIN_TOKEN", "local-test-token")
    monkeypatch.setattr(app_module, "save_data", lambda: None)
    original_products = list(app_module.mock_products)
    try:
        response = client.post(
            "/api/admin/products",
            headers={"Authorization": "Bearer local-test-token"},
            json={
                "id": "local-on-demand-test",
                "title": "كتاب تجريبي حسب الطلب",
                "price": 1800,
                "stock_quantity": 0,
                "availability_type": "on_demand",
                "lead_time_days": 12,
                "featured": True,
            },
        )
        assert response.status_code == 201
        product = response.get_json()
        assert product["availability_type"] == "on_demand"
        assert product["lead_time_days"] == 1
        assert product["featured"] is True
    finally:
        app_module.mock_products[:] = original_products


def test_gift_order_requires_recipient_name() -> None:
    """Gift checkout must collect a recipient before accepting the order."""
    product = next(p for p in app_module.mock_products if p.get("active") and p.get("stock_quantity", 0) > 0)
    response = client.post(
        "/api/orders",
        json={
            "order_type": "gift",
            "gift": {"occasion": "عيد ميلاد"},
            "cart": [{"id": product["id"], "qty": 1}],
            "customer": {"name": "اختبار", "phone": "0550000000", "address": "عنوان تجريبي"},
            "wilaya": 16,
            "delivery_type": "domicile",
        },
    )
    assert response.status_code == 400
    assert "recipient" in response.get_json()["error"]


def test_admin_product_contract_supports_gift_and_discovery_fields(monkeypatch) -> None:
    """Product metadata controls gifting and explainable discovery."""
    monkeypatch.setattr(app_module, "ADMIN_TOKEN", "local-test-token")
    monkeypatch.setattr(app_module, "save_data", lambda: None)
    original_products = list(app_module.mock_products)
    try:
        response = client.post(
            "/api/admin/products",
            headers={"Authorization": "Bearer local-test-token"},
            json={
                "id": "local-gift-metadata-test",
                "title": "كتاب بيانات الهدية",
                "price": 1200,
                "stock_quantity": 4,
                "availability_type": "in_stock",
                "giftable": True,
                "discoverable": True,
                "discovery_tags": ["سريع", "غموض"],
                "gift_tags": ["عيد ميلاد"],
            },
        )
        assert response.status_code == 201
        product = response.get_json()
        assert product["giftable"] is True
        assert product["discovery_tags"] == ["سريع", "غموض"]
        assert product["gift_tags"] == ["عيد ميلاد"]
    finally:
        app_module.mock_products[:] = original_products


def test_mixed_order_separates_personal_and_gift_items() -> None:
    """A mixed cart has one gift group and one personal group with one recipient."""
    products = [p for p in app_module.mock_products if p.get("active") and p.get("stock_quantity", 0) > 0 and p.get("giftable", True)]
    assert len(products) >= 2
    response = client.post(
        "/api/orders",
        json={
            "cart": [
                {"id": products[0]["id"], "qty": 1, "purchase_purpose": "gift"},
                {"id": products[1]["id"], "qty": 1, "purchase_purpose": "personal"},
            ],
            "gift": {"recipient_name": "قارئ التجربة", "recipient_phone": "0550000000", "occasion": "birthday"},
            "customer": {"name": "اختبار", "phone": "0550000000", "address": "عنوان تجريبي"},
            "wilaya": 16,
            "delivery_type": "domicile",
        },
    )
    assert response.status_code == 200
    order_id = response.get_json()["order_id"]
    order = next(order for order in app_module.orders if order["order_id"] == order_id)
    assert order["order_type"] == "mixed"
    assert len(order["gift_items"]) == 1
    assert len(order["personal_items"]) == 1
    assert order["shipping_policy"] == "ship_together"


def test_gift_order_requires_recipient_phone() -> None:
    """Every gift requires a recipient phone number, not only a recipient name."""
    product = next(p for p in app_module.mock_products if p.get("active") and p.get("stock_quantity", 0) > 0 and p.get("giftable", True))
    response = client.post(
        "/api/orders",
        json={
            "cart": [{"id": product["id"], "qty": 1, "purchase_purpose": "gift"}],
            "gift": {"recipient_name": "قارئ التجربة"},
            "customer": {"name": "اختبار", "phone": "0550000000", "address": "عنوان تجريبي"},
            "wilaya": 16,
            "delivery_type": "domicile",
        },
    )
    assert response.status_code == 400
    assert "phone" in response.get_json()["error"]


def test_non_giftable_product_is_rejected_for_gift(monkeypatch) -> None:
    """The backend never trusts the browser's giftability flag."""
    product = next(p for p in app_module.mock_products if p.get("active") and p.get("stock_quantity", 0) > 0)
    original = product.get("giftable", True)
    product["giftable"] = False
    try:
        response = client.post(
            "/api/orders",
            json={
                "cart": [{"id": product["id"], "qty": 1, "purchase_purpose": "gift"}],
                "gift": {"recipient_name": "قارئ التجربة", "recipient_phone": "0550000000"},
                "customer": {"name": "اختبار", "phone": "0550000000", "address": "عنوان تجريبي"},
                "wilaya": 16,
                "delivery_type": "domicile",
            },
        )
        assert response.status_code == 400
        assert "not giftable" in response.get_json()["error"]
    finally:
        product["giftable"] = original


# The browser UI keeps all gift items in one group and the backend records the same policy.
assert app_module.DEFAULT_SETTINGS["features"]["gift_from_cart"] is True
assert app_module.DEFAULT_SETTINGS["features"]["gift_finder"] is True
assert app_module.DEFAULT_SETTINGS["features"]["ideas_lab"] is True
