# Quick Commerce Backend

A high-performance backend system for a quick-commerce platform, built for high-concurrency inventory management and reliable order processing.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy (async) |
| Caching / Queues | Redis |
| Auth | JWT (python-jose) + Bcrypt |
| Migrations | Alembic |
| Server | Uvicorn |

## Project Structure

```
quick-commerce-backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/         # orders, products, inventory, users, dlq
│   │   └── router.py
│   ├── core/                  # config, security, workers, logging
│   ├── db/                    # session, base models
│   ├── models/                # SQLAlchemy models
│   ├── repositories/          # data access layer
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # business logic
│   └── main.py                # app entrypoint
├── admin-dashboard/           # lightweight HTML/JS admin UI
├── scripts/                   # seed, stress tests, load tests
└── alembic/                   # DB migrations
```

## API Endpoints

| Resource | Description |
|---|---|
| `POST /api/v1/orders` | Create and process orders |
| `GET /api/v1/inventory` | Real-time stock levels |
| `POST /api/v1/products` | Product management |
| `GET /api/v1/users` | User management |
| `GET /api/v1/dlq` | Dead-letter queue inspection |

## Getting Started

**Prerequisites:** Python 3.9+, PostgreSQL, Redis

```bash
# Clone and install
git clone https://github.com/shree302001/quick-commerce-backend.git
cd quick-commerce-backend
pip install -r app/api/v1/requirements.txt

# Configure environment
cp .env.example .env   # add DB and Redis credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` (Swagger UI).

## Key Features

- **Real-time inventory** management with concurrency-safe stock updates
- **Reliable order pipeline** with dead-letter queue for failed jobs
- **JWT authentication** with role-based access
- **Async throughout** — built on asyncpg for non-blocking DB access
- **Admin dashboard** for order and inventory monitoring
