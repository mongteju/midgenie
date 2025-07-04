# backend/src/routes/students.py
# Student information related API routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import schemas, models
from ..services import student_service
from ..utils.auth_decorators import get_current_user, has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/students", tags=["Students"])

@router.post("/", response_model=schemas.Student, dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.HOMEROOM_TEACHER]))])
async def create_student(student: schemas.StudentCreate, db: Session = Depends(student_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    if current_user.role == UserRole.HOMEROOM_TEACHER and student.homeroom_teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Homeroom teacher can only create students for themselves.")
    
    db_student = student_service.get_student_by_student_id_number(db, student_id_number=student.student_id_number)
    if db_student:
        raise HTTPException(status_code=400, detail="Student with this ID number already exists")
    return student_service.create_student(db=db, student=student)

@router.get("/", response_model=list[schemas.Student], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.HEAD_TEACHER, UserRole.HOMEROOM_TEACHER]))])
async def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(student_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    if current_user.role == UserRole.HOMEROOM_TEACHER:
        students = student_service.get_students_by_homeroom_teacher(db, teacher_id=current_user.id, skip=skip, limit=limit)
    else:
        students = student_service.get_students(db, skip=skip, limit=limit)
    return students

@router.get("/{student_id}", response_model=schemas.Student, dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.HEAD_TEACHER, UserRole.HOMEROOM_TEACHER, UserRole.STUDENT]))])
async def read_student(student_id: int, db: Session = Depends(student_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    db_student = student_service.get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if current_user.role == UserRole.HOMEROOM_TEACHER and db_student.homeroom_teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view students assigned to you.")
    if current_user.role == UserRole.STUDENT and db_student.id != current_user.id: # Assuming student's user ID is same as student ID
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own profile.")
    
    return db_student
