# Antigravity – Quick Commerce Backend

Backend system for a quick-commerce platform designed for high-concurrency inventory management and reliable order processing.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: PostgreSQL (with [SQLAlchemy](https://www.sqlalchemy.org/) & [asyncpg](https://magicstack.github.io/asyncpg/))
- **Caching/Queues**: [Redis](https://redis.io/)
- **Authentication**: JWT (python-jose) + Bcrypt (passlib)
- **Server**: Uvicorn

## Project Structure

```
d:\quick-commerce-backend\
├── app\
│   ├── api\
│   │   └── v1\
│   │       ├── router.py       # API Routes
│   │       └── requirements.txt # Project Dependencies
│   ├── core\                   # Core configurations
│   ├── db\                     # Database models and sessions
│   ├── services\               # Business logic
│   └── main.py                 # App entrypoint
└── tests\
```

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis

### Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r app/api/v1/requirements.txt
   ```

### Running the App

```bash
uvicorn app.main:app --reload
```

## Features

- **Inventory Correctness**: Real-time stock management.
- **Order Reliability**: Robust processing pipeline.
- **Agent-Assisted Operations**: Tools for support and fulfillment.
