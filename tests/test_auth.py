"""Tests de /auth: registro, login youte rutas protegidas."""
from tests.conftest import auth_headers, register_login


class TestRegister:
    def test_registro_ok_201(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ana@x.com", "password": "secreto123", "name": "Ana"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    def test_email_duplicado_409(self, client):
        for _ in range(2):
            client.post("/api/v1/auth/register", json={"email": "dup@x.com", "password": "secreto123"})
        r = client.post("/api/v1/auth/register", json={"email": "dup@x.com", "password": "otra1234"})
        assert r.status_code == 409

    def test_email_invalido_422(self, client):
        r = client.post("/api/v1/auth/register", json={"email": "no-es-email", "password": "secreto123"})
        assert r.status_code == 422

    def test_password_corta_422(self, client):
        r = client.post("/api/v1/auth/register", json={"email": "ok@x.com", "password": "corta"})
        assert r.status_code == 422


class TestLogin:
    def test_login_ok(self, client):
        register_login(client, "login@x.com")
        r = client.post("/api/v1/auth/login", json={"email": "login@x.com", "password": "secreto123"})
        assert r.status_code == 200
        assert r.json()["access_token"]

    def test_password_mal_401(self, client):
        register_login(client, "mal@x.com")
        r = client.post("/api/v1/auth/login", json={"email": "mal@x.com", "password": "otra1234"})
        assert r.status_code == 401

    def test_email_inexistente_401(self, client):
        r = client.post("/api/v1/auth/login", json={"email": "fantasma@x.com", "password": "secreto123"})
        assert r.status_code == 401


class TestProtected:
    def test_me_sin_token_401(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_token_invalido_401(self, client):
        r = client.get("/api/v1/auth/me", headers=auth_headers("token-falso"))
        assert r.status_code == 401

    def test_me_con_token(self, client):
        token = register_login(client, "yo@x.com")
        r = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["email"] == "yo@x.com"
        assert "hashed_password" not in r.json()

    def test_health_publico(self, client):
        assert client.get("/health").json() == {"status": "ok"}
