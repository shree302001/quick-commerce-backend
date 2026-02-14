from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.logging import LoggingMiddleware
from app.db.session import engine
from app.core.db_events import setup_db_events
from app.core.workers import start_cleanup_worker

# Import all models to ensure they are registered for relationships
from app.models import user, store, product, inventory, order

app = FastAPI(title="Quick Commerce Backend")


@app.on_event("startup")
async def startup_event():
    setup_db_events(engine)
    start_cleanup_worker()


app.add_middleware(LoggingMiddleware)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Quick Commerce Backend"}
