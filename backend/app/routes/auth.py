from fastapi import FastAPI, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from datetime import datetime, timedelta
import jwt
import requests
import os

load_dotenv()

with open("../keys/privjwt.key", "r") as f:
    PRIV_JWT_KEY = f.read()

with open("../keys/pubjwt.key.pub", "r") as f:
    PUBLIC_JWT_KEY=f.read()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def create_jwt(user_email: str):
    expiration = datetime.utcnow() + timedelta(days=7)
    #print(expiration)
    payload = {
        "sub": user_email,
        "exp": expiration,
    }

    return jwt.encode(payload, PRIV_JWT_KEY, algorithm="RS256")

@router.get("/auth/google/login")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

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

    payload = {
        "token": create_jwt(user_info.get("email")),
        "user_info": user_info.json()
    }
    
    return payload