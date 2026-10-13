# ⚡ Tasks API — FastAPI + JWT

API REST de gestión de tareas con **FastAPI**, **SQLModel** y autenticación
**JWT (HS256)**. Proyecto de portafolio pensado para demostrar arquitectura
limpia, tests de extremo a extremo y código listo para producción.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)
![Tests](https://img.shields.io/badge/pytest-21%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Qué demuestra

| Área | Detalle |
|---|---|
| **Autenticación JWT** | `POST /register`, `POST /login`, rutas protegidas con `HTTPBearer` |
| **Aislamiento de datos** | Cada usuario solo ve sus propias tareas (scoping por `owner_id`, 404 en lugar de 403: no filtra existencia) |
| **Validación estricta** | Email con regex, contraseña mínima de 8 chars con 1 dígito, Pydantic v2 |
| **Filtrado y paginación** | `?status=&priority=&q=&skip=&limit=` con respuesta `TaskList` estándar |
| **Arquitectura** | `models` (SQL) separados de `schemas` (API); routers por dominio; DI con `Depends` |
| **Robustez** | Contraseñas con `passlib/bcrypt` (+ fallback PBKDF2 automático), `JWT_SECRET` obligatoria en producción |
| **Calidad** | 21 tests, sin deprecaciones, base de datos efímera por test |

---

## 🚀 Inicio rápido

```bash
cd tasks-api-fastapi
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Docs interactivas (Swagger): **http://127.0.0.1:8000/docs**

### Variables de entorno (opcionales)

```env
DATABASE_URL=sqlite:///./tasks.db   # soporta cualquier driver de SQLAlchemy
JWT_SECRET=...                      # obligatoria si ENV=production
ENV=dev
JWT_EXPIRES_MIN=30
CORS_ORIGINS=*                      # csv separado: http://a.com,http://b.com
```

---

## 📡 Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | — | Liveness |
| POST | `/api/v1/auth/register` | — | 201 + Token |
| POST | `/api/v1/auth/login` | — | 200 + Token |
| GET | `/api/v1/auth/me` | ✅ | Perfil del usuario del token |
| POST | `/api/v1/tasks` | ✅ | 201 TaskOut |
| GET | `/api/v1/tasks` | ✅ | Lista filtrada + paginada |
| GET | `/api/v1/tasks/{id}` | ✅ | 200 / 404 |
| PATCH | `/api/v1/tasks/{id}` | ✅ | Actualización parcial |
| DELETE | `/api/v1/tasks/{id}` | ✅ | 204 / 404 |

### Ejemplo con cURL

```bash
# Registro → token
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@x.com","password":"secreto123","name":"Ana"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Crear tarea
curl -X POST localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Terminar el portafolio","priority":"high","due_date":"2026-10-20"}'

# Listar con filtro
curl "localhost:8000/api/v1/tasks?priority=high&status=pending" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Tests

```bash
pytest -v          # 21 tests: auth, CRUD, aislamiento, filtros, paginación
```

La suite corre sin red y con una base efímera por test (drop/create).

---

## 🏗️ Estructura

```
tasks-api-fastapi/
├── app/
│   ├── main.py            # App FastAPI + lifespan + CORS
│   ├── config.py          # Settings 12-factor (env, con validaciones)
│   ├── database.py        # Engine/Session + create_all
│   ├── models.py          # User, Task (SQLModel, enums)
│   ├── schemas.py         # DTOs Pydantic v2 (validadores propios)
│   ├── security.py        # bcrypt/PBKDF2 + JWT HS256
│   └── routers/
│       ├── auth.py        # register / login / me
│       └── tasks.py       # CRUD scoping por owner
├── tests/
│   ├── conftest.py        # BD temporal + TestClient
│   ├── test_auth.py
│   └── test_tasks.py
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── .github/workflows/ci.yml
├── LICENSE
└── README.md
```

---

## 🐳 Docker

```bash
docker build -t tasks-api .
docker run -p 8000:8000 -e JWT_SECRET=changeme tasks-api
```

---

## 📜 Licencia

MIT — ver [LICENSE](LICENSE).
