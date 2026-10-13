"""Tests de /tasks: CRUD, aislamiento, filtros y paginación."""
import datetime as dt

from tests.conftest import auth_headers, register_login


def make_task(client, token: str, title: str, **extra) -> dict:
    payload = {"title": title, **extra}
    r = client.post("/api/v1/tasks", json=payload, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    return r.json()


class TestCreateRead:
    def test_crear_y_leer(self, client):
        token = register_login(client)
        task = make_task(
            client, token, "Publicar post",
            description="Blog técnico", status="in_progress",
            priority="high", due_date="2026-10-20",
        )
        r = client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(token))
        assert r.status_code == 200
        got = r.json()
        assert got["title"] == "Publicar post"
        assert got["status"] == "in_progress"
        assert got["priority"] == "high"
        assert got["due_date"] == "2026-10-20"

    def test_401_sin_token(self, client):
        assert client.get("/api/v1/tasks").status_code == 401
        assert client.post("/api/v1/tasks", json={"title": "x"}).status_code == 401

    def test_404_tarea_inexistente(self, client):
        token = register_login(client)
        r = client.get("/api/v1/tasks/9999", headers=auth_headers(token))
        assert r.status_code == 404


class TestOwnership:
    def test_usuario_b_no_ve_tareas_de_a(self, client):
        token_a = register_login(client, "a@x.com")
        token_b = register_login(client, "b@x.com")
        task = make_task(client, token_a, "Tarea de A")

        # Lista de B no contiene la de A
        r = client.get("/api/v1/tasks", headers=auth_headers(token_b))
        assert [t["id"] for t in r.json()["items"]] == []

        # Y no puede manipularla directamente
        assert client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(token_b)).status_code == 404
        assert client.patch(
            f"/api/v1/tasks/{task['id']}", json={"title": "hack"}, headers=auth_headers(token_b)
        ).status_code == 404
        assert client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers(token_b)).status_code == 404


class TestUpdateDelete:
    def test_patch_parcial(self, client):
        token = register_login(client)
        task = make_task(client, token, "Original")
        r = client.patch(
            f"/api/v1/tasks/{task['id']}", json={"status": "done"}, headers=auth_headers(token)
        )
        assert r.status_code == 200
        assert r.json()["status"] == "done"
        assert r.json()["title"] == "Original"

    def test_delete(self, client):
        token = register_login(client)
        task = make_task(client, token, "Borrar")
        assert client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers(token)).status_code == 204
        assert client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers(token)).status_code == 404


class TestFiltersPagination:
    def _seed(self, client) -> str:
        token = register_login(client, "seed@x.com")
        make_task(client, token, "Escribir API", status="done", priority="high")
        make_task(client, token, "Escribir test", status="pending", priority="low")
        make_task(client, token, "Guardar dinero", description="compras online", status="pending")
        return token

    def test_filtro_por_status(self, client):
        token = self._seed(client)
        r = client.get("/api/v1/tasks?status=pending", headers=auth_headers(token))
        assert r.json()["total"] == 2
        assert all(t["status"] == "pending" for t in r.json()["items"])

    def test_filtro_por_prioridad(self, client):
        token = self._seed(client)
        r = client.get("/api/v1/tasks?priority=high", headers=auth_headers(token))
        assert r.json()["total"] == 1

    def test_busqueda_q(self, client):
        token = self._seed(client)
        r = client.get("/api/v1/tasks?q=test", headers=auth_headers(token))
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["title"] == "Escribir test"

    def test_paginacion(self, client):
        token = self._seed(client)
        r = client.get("/api/v1/tasks?limit=2&skip=0", headers=auth_headers(token))
        body = r.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        r2 = client.get("/api/v1/tasks?limit=2&skip=2", headers=auth_headers(token))
        assert len(r2.json()["items"]) == 1
        assert r.json()["items"][0]["id"] != r2.json()["items"][0]["id"]
