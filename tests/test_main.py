from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def get_auth_token():
    """Helper: signs up and logs in a fresh test user, returns access token"""
    import uuid
    email = f"test_{uuid.uuid4().hex[:8]}@gmail.com"
    client.post("/signup", json={"email": email, "password": "testpass123"})
    response = client.post("/login", json={"email": email, "password": "testpass123"})
    return response.json()["access_token"]


def test_signup_success():
    import uuid
    email = f"pytest_{uuid.uuid4().hex[:8]}@gmail.com"
    response = client.post("/signup", json={"email": email, "password": "testpass123"})
    assert response.status_code == 200
    assert "user_id" in response.json()


def test_signup_invalid_email():
    response = client.post("/signup", json={"email": "not-a-real-email", "password": "testpass123"})
    assert response.status_code == 422


def test_login_wrong_password():
    import uuid
    email = f"wrongpass_{uuid.uuid4().hex[:8]}@gmail.com"
    client.post("/signup", json={"email": email, "password": "correctpass"})
    response = client.post("/login", json={"email": email, "password": "wrongpass"})
    assert response.status_code == 401


def test_create_product_requires_auth():
    response = client.post("/products", json={"name": "Test Saree", "category": "Saree", "price": 1000, "quantity": 5})
    assert response.status_code == 401


def test_create_and_get_product():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/products",
        json={"name": "Banarasi Saree", "category": "Saree", "price": 2500, "quantity": 10},
        headers=headers,
    )
    assert create_response.status_code == 200
    product_id = create_response.json()["id"]

    get_response = client.get(f"/products/{product_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Banarasi Saree"


def test_negative_quantity_rejected():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/products",
        json={"name": "Bad Product", "category": "Suit", "price": 500, "quantity": -5},
        headers=headers,
    )
    assert response.status_code == 422


def test_stock_adjustment():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/products",
        json={"name": "Cotton Suit", "category": "Suit", "price": 1200, "quantity": 5},
        headers=headers,
    )
    product_id = create_response.json()["id"]

    response = client.patch(f"/products/{product_id}/stock", json={"change": -2}, headers=headers)
    assert response.status_code == 200
    assert response.json()["quantity"] == 3


def test_stock_cannot_go_below_zero():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/products",
        json={"name": "Low Stock Item", "category": "Dupatta", "price": 300, "quantity": 1},
        headers=headers,
    )
    product_id = create_response.json()["id"]

    response = client.patch(f"/products/{product_id}/stock", json={"change": -5}, headers=headers)
    assert response.status_code == 400