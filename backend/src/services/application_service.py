# backend/src/services/application_service.py
# Business logic for student application operations

from sqlalchemy.orm import Session
from ..database import models, schemas

def get_db():
    # Placeholder for DB session
    yield None

def get_student(db: Session, student_id: int):
    # return db.query(models.Student).filter(models.Student.id == student_id).first()
    return None

def get_student_application(db: Session, application_id: int):
    # return db.query(models.StudentApplication).filter(models.StudentApplication.id == application_id).first()
    return None

def get_application_by_student_id(db: Session, student_id: int):
    # return db.query(models.StudentApplication).filter(models.StudentApplication.student_id == student_id).first()
    return None

def create_student_application(db: Session, application: schemas.StudentApplicationCreate):
    db_application = models.StudentApplication(
        student_id=application.student_id,
        school_id=application.school_id,
        is_accepted=application.is_accepted
    )
    # db.add(db_application)
    # db.commit()
    # db.refresh(db_application)
    return db_application

def update_student_application(db: Session, application: models.StudentApplication, application_update: schemas.StudentApplicationCreate):
    application.school_id = application_update.school_id
    application.is_accepted = application_update.is_accepted
    # db.commit()
    # db.refresh(application)
    return application
