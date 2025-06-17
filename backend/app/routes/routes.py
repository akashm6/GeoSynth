from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/ping")
def ping():
    return {"msg": "pong"}