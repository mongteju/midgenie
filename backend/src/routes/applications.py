# backend/src/routes/applications.py
# High school application and acceptance status (Homeroom Teacher only)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import schemas, models
from ..services import application_service
from ..utils.auth_decorators import get_current_user, has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=schemas.StudentApplication, dependencies=[Depends(has_role([UserRole.HOMEROOM_TEACHER]))])
async def create_student_application(application: schemas.StudentApplicationCreate, db: Session = Depends(application_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    # Ensure the homeroom teacher is managing their own student
    student = application_service.get_student(db, application.student_id)
    if not student or student.homeroom_teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage applications for your assigned students.")
    
    db_application = application_service.get_application_by_student_id(db, student_id=application.student_id)
    if db_application:
        raise HTTPException(status_code=400, detail="Student already has an application record.")
    
    return application_service.create_student_application(db=db, application=application)

@router.put("/{application_id}", response_model=schemas.StudentApplication, dependencies=[Depends(has_role([UserRole.HOMEROOM_TEACHER]))])
async def update_student_application(application_id: int, application_update: schemas.StudentApplicationCreate, db: Session = Depends(application_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    db_application = application_service.get_student_application(db, application_id=application_id)
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Ensure the homeroom teacher is managing their own student's application
    student = application_service.get_student(db, db_application.student_id)
    if not student or student.homeroom_teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage applications for your assigned students.")
    
    return application_service.update_student_application(db=db, application=db_application, application_update=application_update)

@router.get("/students/{student_id}", response_model=schemas.StudentApplication, dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.HEAD_TEACHER, UserRole.HOMEROOM_TEACHER, UserRole.STUDENT]))])
async def get_student_application(student_id: int, db: Session = Depends(application_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    # Authorization logic similar to grades
    if current_user.role == UserRole.HOMEROOM_TEACHER:
        student = application_service.get_student(db, student_id)
        if not student or student.homeroom_teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view this student's application.")
    elif current_user.role == UserRole.STUDENT:
        if student_id != current_user.id: # Needs refinement for actual user-student mapping
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own application.")

    application = application_service.get_application_by_student_id(db, student_id=student_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found for this student.")
    return application
