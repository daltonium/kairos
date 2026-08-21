from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "companies", "status": "ok"}