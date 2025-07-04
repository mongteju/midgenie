# backend/src/routes/auth.py
# Authentication related API routes

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import models, schemas
from ..services import auth_service
from ..utils.auth_decorators import get_current_user, has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth_service.get_db)):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.UserInDB, dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def register_user(user: schemas.UserCreate, db: Session = Depends(auth_service.get_db)):
    db_user = auth_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return auth_service.create_user(db=db, user=user)

@router.put("/users/{user_id}/role", response_model=schemas.UserInDB, dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def update_user_role(user_id: int, user_role: schemas.UserUpdateRole, db: Session = Depends(auth_service.get_db)):
    db_user = auth_service.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return auth_service.update_user_role(db=db, user=db_user, new_role=user_role.role)

@router.get("/me", response_model=schemas.UserInDB)
async def read_users_me(current_user: schemas.UserInDB = Depends(get_current_user)):
    return current_user
