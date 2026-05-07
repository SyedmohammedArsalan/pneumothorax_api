# auth.py - JWT Authentication Module
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import sqlite3
import os

# =====================================================
# CONFIGURATION (change SECRET_KEY in production!)
# =====================================================
SECRET_KEY = "change-this-to-a-random-secret-key-in-production-please"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# =====================================================
# PYDANTIC MODELS
# =====================================================
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

# =====================================================
# PASSWORD HELPERS
# =====================================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# =====================================================
# JWT HELPERS
# =====================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# =====================================================
# DATABASE USER OPERATIONS
# =====================================================
def get_user_by_username(username: str):
    con = sqlite3.connect("pneumoai.db")
    con.row_factory = sqlite3.Row
    user = con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    con.close()
    return dict(user) if user else None

def get_user_by_email(email: str):
    con = sqlite3.connect("pneumoai.db")
    con.row_factory = sqlite3.Row
    user = con.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    con.close()
    return dict(user) if user else None

def create_user(username: str, email: str, hashed_password: str):
    con = sqlite3.connect("pneumoai.db")
    con.execute("""
        INSERT INTO users (username, email, hashed_password, created_at)
        VALUES (?, ?, ?, ?)
    """, (username, email, hashed_password, datetime.now().isoformat()))
    con.commit()
    user_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    con.close()
    return user_id

# =====================================================
# DEPENDENCY: GET CURRENT USER FROM TOKEN
# =====================================================
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserInDB(**user)