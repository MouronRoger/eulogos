"""Security middleware and utilities for authentication and authorization.

This module provides security-related functionality including:
- JWT token-based authentication
- Role-based access control with scopes
- Rate limiting middleware using token bucket algorithm
- Password hashing utilities
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = "your-secret-key-here"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    """Token model."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""

    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    """User model."""

    username: str
    disabled: Optional[bool] = None
    scopes: List[str] = []


class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(self, rate: float, capacity: int):
        """Initialize rate limiter.

        Args:
            rate: Tokens per second
            capacity: Maximum token bucket size
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Attempt to acquire a token.

        Returns:
            bool: True if token acquired, False otherwise
        """
        async with self._lock:
            now = time.time()
            # Add new tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


class RateLimitMiddleware:
    """Middleware for rate limiting."""

    def __init__(self, rate: float = 10.0, capacity: int = 10):
        """Initialize rate limit middleware.

        Args:
            rate: Requests per second
            capacity: Maximum burst size
        """
        self.limiters: Dict[str, RateLimiter] = {}
        self.rate = rate
        self.capacity = capacity
        self._lock = asyncio.Lock()

    async def get_limiter(self, key: str) -> RateLimiter:
        """Get or create rate limiter for key."""
        async with self._lock:
            if key not in self.limiters:
                self.limiters[key] = RateLimiter(self.rate, self.capacity)
            return self.limiters[key]

    async def __call__(self, request: Request, call_next):
        """Apply rate limiting middleware."""
        # Get client identifier (IP address or API key)
        client_id = request.client.host

        # Get rate limiter for this client
        limiter = await self.get_limiter(client_id)

        # Try to acquire token
        if not await limiter.acquire():
            logger.warning(f"Rate limit exceeded for client {client_id}")
            raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "1"})

        # Process request
        response = await call_next(request)
        return response


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, scopes=payload.get("scopes", []))
    except JWTError:
        raise credentials_exception

    # In a real application, you would look up the user in a database
    # This is just a simple example
    user = User(username=token_data.username, scopes=token_data.scopes)
    if user is None:
        raise credentials_exception
    return user


def requires_scope(required_scopes: List[str]):
    """Check required scopes for endpoint access."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            for scope in required_scopes:
                if scope not in current_user.scopes:
                    raise HTTPException(status_code=403, detail=f"Permission denied. Required scope: {scope}")
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


# Example usage in FastAPI app:
"""
from fastapi import FastAPI
from app.middleware.security import RateLimitMiddleware, requires_scope

app = FastAPI()

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate user credentials (implement your own logic)
    user_data = {"sub": form_data.username, "scopes": ["read:texts", "export:texts"]}
    access_token = create_access_token(user_data)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/api/v2/export/{urn}")
@requires_scope(["export:texts"])
async def export_text(urn: str, current_user: User = Depends(get_current_user)):
    # Your export logic here
    return {"message": "Export successful"}
"""
