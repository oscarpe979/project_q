from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import upload, auth

from contextlib import asynccontextmanager
from backend.app.database import create_db_and_tables
from backend.app import models # Import models to register them with SQLModel
from backend.app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Royal Caribbean Scheduler API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(upload.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Royal Caribbean Scheduler API"}
