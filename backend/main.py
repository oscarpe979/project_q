from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import upload

app = FastAPI(title="Royal Caribbean Scheduler API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Royal Caribbean Scheduler API"}
