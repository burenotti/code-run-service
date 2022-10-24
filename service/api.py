from fastapi import APIRouter

router = APIRouter(
    prefix="/code",
    tags=["Code", "Execution"],
)
