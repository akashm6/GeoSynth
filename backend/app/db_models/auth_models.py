from sqlalchemy import create_engine, text
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class UserModel(BaseModel):
    email: str
    username: str
    password: str
    date_created: datetime

class TokenModel(BaseModel):
    jwt_token: str
    date_created: datetime
    date_expired: datetime
    is_valid: bool
    has_been_used: bool
    