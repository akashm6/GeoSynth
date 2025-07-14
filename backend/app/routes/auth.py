from fastapi import FastAPI, HTTPException, APIRouter

router = APIRouter()

@router.get("/confirmLogin")
def checkPassword():
    return "Checking Login"