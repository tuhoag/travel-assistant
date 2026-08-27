from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthCheckResponse(BaseModel):
    status: str

@router.get("/health")
def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="healthy")
