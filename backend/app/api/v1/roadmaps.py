from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "roadmaps", "status": "ok"}