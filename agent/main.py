from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import health_router, threads_router

app = FastAPI(title="Travel Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(threads_router)