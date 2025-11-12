
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field
from jwt import PyJWTError
import jwt
from backend.config import MONGO_URI, DB_NAME, USERS_COLLECTION, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(prefix="/auth", tags=["auth"])   
password_hasher = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

mongo_client = AsyncIOMotorClient(MONGO_URI)
users_collection = mongo_client[DB_NAME][USERS_COLLECTION]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserRead(BaseModel):
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": subject}
    expire_delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError as exc:
        raise credentials_exception from exc

    user_record = await users_collection.find_one({"_id": username})
    if user_record is None:
        raise credentials_exception

    return UserRead(username=user_record["_id"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate) -> UserRead:
    hashed_password = get_password_hash(user.password)
    document = {
        #TODO change to ObjectId
        "_id": user.username,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await users_collection.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Username already registered"},
        ) from exc

    return UserRead(username=user.username)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user_record = await users_collection.find_one({"_id": form_data.username})
    if (
        not user_record
        or not verify_password(form_data.password, user_record["hashed_password"])
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Incorrect username or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=form_data.username)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    return current_user

