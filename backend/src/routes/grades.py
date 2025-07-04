# backend/src/routes/grades.py
# Grade file upload (Head Teacher only)

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from ..database import schemas, models
from ..services import grade_service
from ..utils.auth_decorators import get_current_user, has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/grades", tags=["Grades"])

@router.post("/upload", dependencies=[Depends(has_role([UserRole.HEAD_TEACHER]))])
async def upload_grades_file(file: UploadFile = File(...), db: Session = Depends(grade_service.get_db)):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV and XLSX are allowed.")
    
    try:
        # In a real application, you would parse the file and save grades to DB
        # For now, just a placeholder
        content = await file.read()
        # Process content, e.g., parse CSV/XLSX and save to database
        # grade_service.process_grades_file(db, content, file.filename)
        return {"message": f"File '{file.filename}' uploaded successfully. Processing grades..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")

@router.get("/students/{student_id}", response_model=list[schemas.Grade], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.HEAD_TEACHER, UserRole.HOMEROOM_TEACHER, UserRole.STUDENT]))])
async def get_student_grades(student_id: int, db: Session = Depends(grade_service.get_db), current_user: schemas.UserInDB = Depends(get_current_user)):
    # Authorization logic:
    # Admin/Head Teacher can view all grades
    # Homeroom Teacher can view grades of their assigned students
    # Student can view their own grades
    
    if current_user.role == UserRole.HOMEROOM_TEACHER:
        student = grade_service.get_student(db, student_id)
        if not student or student.homeroom_teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view these grades.")
    elif current_user.role == UserRole.STUDENT:
        # Assuming student's user ID is linked to student_id
        # This needs proper linking in the User and Student models
        # For now, a simple check:
        if student_id != current_user.id: # This needs to be refined based on actual user-student mapping
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own grades.")

    grades = grade_service.get_grades_by_student_id(db, student_id=student_id)
    return grades
