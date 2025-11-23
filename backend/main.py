from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import upload

from contextlib import asynccontextmanager
from backend.app.database import create_db_and_tables
from backend.app import models # Import models to register them with SQLModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Royal Caribbean Scheduler API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Royal Caribbean Scheduler API"}
