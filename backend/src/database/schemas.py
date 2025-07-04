# backend/src/database/schemas.py
# Data validation and serialization/deserialization schemas (e.g., Pydantic schemas)

from pydantic import BaseModel, EmailStr
from typing import Optional
from .models import UserRole

class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.STUDENT # Default role for new users

class UserUpdateRole(BaseModel):
    role: UserRole

class UserInDB(UserBase):
    id: int
    is_active: bool
    role: UserRole

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class StudentBase(BaseModel):
    name: str
    student_id_number: str
    homeroom_teacher_id: Optional[int] = None

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    class Config:
        orm_mode = True

class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None

class SchoolCreate(SchoolBase):
    pass

class School(SchoolBase):
    id: int
    class Config:
        orm_mode = True

class GradeBase(BaseModel):
    subject: str
    score: int

class GradeCreate(GradeBase):
    student_id: int

class Grade(GradeBase):
    id: int
    student_id: int
    class Config:
        orm_mode = True

class StudentApplicationBase(BaseModel):
    student_id: int
    school_id: Optional[int] = None
    is_accepted: bool = False

class StudentApplicationCreate(StudentApplicationBase):
    pass

class StudentApplication(StudentApplicationBase):
    id: int
    class Config:
        orm_mode = True
