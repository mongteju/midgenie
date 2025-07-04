# backend/src/services/grade_service.py
# Business logic for grade operations

from sqlalchemy.orm import Session
from ..database import models, schemas

def get_db():
    # Placeholder for DB session
    yield None

def get_student(db: Session, student_id: int):
    # return db.query(models.Student).filter(models.Student.id == student_id).first()
    return None

def get_grades_by_student_id(db: Session, student_id: int):
    # return db.query(models.Grade).filter(models.Grade.student_id == student_id).all()
    return []

def process_grades_file(db: Session, file_content: bytes, filename: str):
    # This function would parse the file_content (CSV/XLSX)
    # and save the grades to the database.
    # Example (simplified):
    # import pandas as pd
    # if filename.endswith('.csv'):
    #     df = pd.read_csv(io.BytesIO(file_content))
    # elif filename.endswith('.xlsx'):
    #     df = pd.read_excel(io.BytesIO(file_content))
    #
    # for index, row in df.iterrows():
    #     grade = models.Grade(student_id=row['student_id'], subject=row['subject'], score=row['score'])
    #     db.add(grade)
    # db.commit()
    pass
