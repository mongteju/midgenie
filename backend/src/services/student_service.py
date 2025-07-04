# backend/src/services/student_service.py
# Business logic for student operations

from sqlalchemy.orm import Session
from ..database import models, schemas

def get_db():
    # Placeholder for DB session
    yield None

def get_student(db: Session, student_id: int):
    # return db.query(models.Student).filter(models.Student.id == student_id).first()
    return None

def get_student_by_student_id_number(db: Session, student_id_number: str):
    # return db.query(models.Student).filter(models.Student.student_id_number == student_id_number).first()
    return None

def get_students(db: Session, skip: int = 0, limit: int = 100):
    # return db.query(models.Student).offset(skip).limit(limit).all()
    return []

def get_students_by_homeroom_teacher(db: Session, teacher_id: int, skip: int = 0, limit: int = 100):
    # return db.query(models.Student).filter(models.Student.homeroom_teacher_id == teacher_id).offset(skip).limit(limit).all()
    return []

def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(name=student.name, student_id_number=student.student_id_number, homeroom_teacher_id=student.homeroom_teacher_id)
    # db.add(db_student)
    # db.commit()
    # db.refresh(db_student)
    return db_student
