import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from backend.database import get_db_cursor
from backend.schemas import UserRegister, UserLogin, UserResponse, Token
from backend.auth import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister):
    """Registers a new student or teacher account in the cloud database."""
    email_clean = payload.email.lower().strip()
    with get_db_cursor() as cursor:
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO users (user_id, name, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            payload.name.strip(),
            email_clean,
            get_password_hash(payload.password),
            payload.role.lower(),
            created_at
        ))

    return {
        "user_id": user_id,
        "name": payload.name.strip(),
        "email": email_clean,
        "role": payload.role.lower(),
        "created_at": created_at
    }

@router.post("/login", response_model=Token)
def login_user(payload: UserLogin):
    """Authenticates user credentials and issues a signed JWT Bearer token."""
    email_clean = payload.email.lower().strip()
    with get_db_cursor() as cursor:
        cursor.execute("SELECT user_id, name, email, password_hash, role, created_at FROM users WHERE email = ?", (email_clean,))
        user = cursor.fetchone()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_claims = {
        "sub": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"]
    }
    token = create_access_token(data=token_claims)

    user_resp = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"]
    }

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_resp
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    return current_user
