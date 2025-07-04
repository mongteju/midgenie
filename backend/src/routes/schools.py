# backend/src/routes/schools.py
# School information related API routes

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import schemas, models
from ..services import school_service
from ..utils.auth_decorators import get_current_user, has_role
from ..utils.constants import UserRole

router = APIRouter(prefix="/schools", tags=["Schools"])

@router.post("/", response_model=schemas.School, dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def create_school(school: schemas.SchoolCreate, db: Session = Depends(school_service.get_db)):
    db_school = school_service.get_school_by_name(db, name=school.name)
    if db_school:
        raise HTTPException(status_code=400, detail="School with this name already exists")
    return school_service.create_school(db=db, school=school)

@router.get("/", response_model=list[schemas.School])
async def read_schools(skip: int = 0, limit: int = 100, db: Session = Depends(school_service.get_db)):
    schools = school_service.get_schools(db, skip=skip, limit=limit)
    return schools

@router.get("/{school_id}", response_model=schemas.School)
async def read_school(school_id: int, db: Session = Depends(school_service.get_db)):
    db_school = school_service.get_school(db, school_id=school_id)
    if db_school is None:
        raise HTTPException(status_code=404, detail="School not found")
    return db_school
