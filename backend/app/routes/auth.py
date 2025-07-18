from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import APIRouter
from pathlib import Path
import requests
import jwt
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
priv_key_path = BASE_DIR / "app" / "keys" / "privjwt.key"

with open(priv_key_path, "r") as f:
    PRIV_JWT_KEY = f.read()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def create_jwt(user_email: str):
    expiration = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": user_email,
        "exp": expiration,
    }

    return jwt.encode(payload, PRIV_JWT_KEY, algorithm="RS256")

@router.get("/auth/google/redirect")
def auth_and_redirect(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    res = requests.post(token_url, data = data)
    if not res.ok:
        return {
            "message": "Invalid credentials. Try again."
        }
    
    access_token = res.json().get("access_token")
    user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
    user_data = user_info.json()

    payload = {
        "token": create_jwt(user_data.get("email")),
        "user_data": user_data
    }

    return payload