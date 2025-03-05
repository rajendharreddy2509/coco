from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import secrets
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from database import get_db_connection
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load SECRET_KEY safely from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("🚨 SECRET_KEY is missing! Set it in the .env file.")

# Token expiration time (24 hours)
TOKEN_EXPIRE_MINUTES = 60 * 24

# In-memory token storage (replace with Redis or a database in production)
active_tokens: Dict[str, Dict] = {}

class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

def hash_password(password: str) -> str:
    """Hash the user's password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the provided password against the stored hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_token(user_id: int) -> str:
    """
    Generate a simple secure token for authentication
    """
    # Create a random token
    random_bytes = secrets.token_bytes(32)
    token = base64.urlsafe_b64encode(random_bytes).decode()
    
    # Store token with user_id and expiration time
    expiration = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    active_tokens[token] = {
        "user_id": user_id,
        "expires": expiration
    }
    
    return token

def verify_token(token: str) -> Optional[int]:
    """
    Verify a token and return the user_id if valid
    """
    if token not in active_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    token_data = active_tokens[token]
    
    # Check if token has expired
    if datetime.utcnow() > token_data["expires"]:
        del active_tokens[token]  # Remove expired token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    return token_data["user_id"]

def insert_user_into_db(user: UserSignup, conn) -> int:
    """Insert a new user into the database and return their user ID."""
    hashed_password = hash_password(user.password)
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id",
                        (user.name, user.email, hashed_password))
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"🚨 Signup error: {str(e)}")

def get_user_by_email(email: str, conn):
    """Retrieve user details by email from the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
        return cur.fetchone()

@router.post("/signup")
async def signup(user: UserSignup, conn=Depends(get_db_connection)):
    """Register a new user."""
    user_id = insert_user_into_db(user, conn)
    return {"message": "✅ User registered successfully!", "user_id": user_id}

@router.post("/login")
async def login(user: UserLogin, conn=Depends(get_db_connection)):
    """Authenticate user and return a token."""
    result = get_user_by_email(user.email, conn)
    if not result:
        raise HTTPException(status_code=401, detail="🚫 Invalid email or password.")
    
    user_id, name, stored_password = result
    
    if not verify_password(user.password, stored_password):
        raise HTTPException(status_code=401, detail="🚫 Invalid email or password.")
    
    token = generate_token(user_id)
    return {"token": token, "message": f"✅ Welcome {name}!"}

# Add this dependency to protect routes that require authentication
def get_current_user_id(authorization: str = Depends(lambda x: x.headers.get("Authorization"))):
    """
    Dependency to validate token and get the current user ID.
    Use this to protect routes that require authentication.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.replace("Bearer ", "")
    user_id = verify_token(token)
    return user_id

# Example of a protected route:
# @router.get("/protected")
# async def protected_route(user_id: int = Depends(get_current_user_id)):
#     return {"message": "This is a protected route", "user_id": user_id}