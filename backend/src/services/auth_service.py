# backend/src/services/auth_service.py
# Business logic for authentication

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..database import models, schemas
from ..config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    # This is a placeholder for actual DB session management
    # In a real FastAPI app, you'd use `Depends` with a function
    # that yields a SQLAlchemy session.
    # Example:
    # from sqlalchemy import create_engine
    # from sqlalchemy.orm import sessionmaker
    # SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    # engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    yield None # Placeholder

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_user(db: Session, user_id: int):
    # Placeholder: In a real app, query DB
    # return db.query(models.User).filter(models.User.id == user_id).first()
    return None

def get_user_by_username(db: Session, username: str):
    # Placeholder: In a real app, query DB
    # return db.query(models.User).filter(models.User.username == username).first()
    return None

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, email=user.email, full_name=user.full_name, role=user.role)
    # Placeholder: In a real app, add to DB and commit
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)
    return db_user

def update_user_role(db: Session, user: models.User, new_role: models.UserRole):
    user.role = new_role
    # Placeholder: In a real app, commit changes
    # db.commit()
    # db.refresh(user)
    return user

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return schemas.UserInDB.from_orm(user) # Convert to Pydantic model
