from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from app.db import engine, text, SessionLocal
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from dotenv import load_dotenv
from pathlib import Path
import requests
import jwt
import base64
import os

load_dotenv()

PRIV_JWT_KEY = base64.b64decode(os.getenv("PRIV_JWT_KEY")).decode("utf-8")
PUBLIC_JWT_KEY = base64.b64decode(os.getenv("PUBLIC_JWT_KEY")).decode("utf-8")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# use this to validate jwt's with frontend payloads
class JWTModel(BaseModel):
    token: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/create-jwt")
def create_jwt(user_email: str, db: Session = Depends(get_db)):

    if not check_user_exists(user_email, db):
        create_new_user(user_email, db)

    expiration = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": user_email,
        "exp": expiration,
    }

    return jwt.encode(payload, PRIV_JWT_KEY, algorithm="RS256")

@router.get("/check-user-exists")
def check_user_exists(user_email: str, db: Session = Depends(get_db)):

    exists_query = text("""
    SELECT 1 FROM user_table 
    WHERE email = :user_email
    LIMIT 1;
    """)

    result = db.execute(exists_query, {"user_email": user_email}).scalar()

    return result is not None

@router.get("/create-new-user")
def create_new_user(user_email: str, db: Session = Depends(get_db)):

    date_created = datetime.utcnow().isoformat()
    username = user_email.split("@")[0]

    insert_query = text("""
    INSERT INTO user_table (email, username, date_created)  
    VALUES (:user_email, :username, :date_created);
    """)

    params = {
        "user_email": user_email,
        "username": username,
        "date_created": date_created
    }
    try:
        db.execute(insert_query, params)
        db.commit()
        return {"message": "User inserted!"}
    
    except Exception as e:
        return {"message" : e}


@router.get("/auth/google/redirect")
def auth_and_redirect(code: str, db: Session = Depends(get_db)):
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
        "token": create_jwt(user_data.get("email"), db),
        "user_data": user_data
    }

    return payload

@router.post("/validate-token")
def validate_token(token_info: JWTModel):

    try:
        decoded_token = jwt.decode(
            token_info.token, 
            key = PUBLIC_JWT_KEY, 
            algorithms="RS256")

        return True
    
    except jwt.ExpiredSignatureError:
        return False
    
    except jwt.InvalidTokenError:
        return False

