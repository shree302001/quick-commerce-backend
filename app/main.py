from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.logging import LoggingMiddleware
from app.db.session import engine
from app.core.db_events import setup_db_events
from app.core.workers import start_cleanup_worker

# Import all models to ensure they are registered for relationships
from app.models import user, store, product, inventory, order

app = FastAPI(title="Quick Commerce Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to Quick Commerce Backend"}
