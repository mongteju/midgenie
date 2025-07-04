# backend/src/utils/auth_decorators.py
# Role-based access control decorators

from fastapi import Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from ..database import schemas
from ..services.auth_service import get_current_user_from_token, get_db
from ..utils.constants import UserRole

def get_current_user(token: str = Depends(get_current_user_from_token)):
    return token

def has_role(roles: List[UserRole]):
    def role_checker(current_user: schemas.UserInDB = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
