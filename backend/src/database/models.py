# backend/src/database/models.py
# Database model definitions (e.g., SQLAlchemy, Pydantic models)

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HEAD_TEACHER = "head_teacher" # 부장선생님
    HOMEROOM_TEACHER = "homeroom_teacher" # 담임선생님
    STUDENT = "student"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    students = relationship("Student", back_populates="homeroom_teacher", uselist=False) # For homeroom teachers

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    student_id_number = Column(String, unique=True, index=True) # 학번
    homeroom_teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True) # 담임선생님 ID
    
    homeroom_teacher = relationship("User", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    applications = relationship("StudentApplication", back_populates="student")

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    address = Column(String, nullable=True)
    # Add other school-related fields as needed

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String)
    score = Column(Integer)
    # Add other grade-related fields (e.g., semester, year)

    student = relationship("Student", back_populates="grades")

class StudentApplication(Base):
    __tablename__ = "student_applications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True) # 지원 고등학교 ID
    is_accepted = Column(Boolean, default=False) # 합격 여부

    student = relationship("Student", back_populates="applications")
    school = relationship("School")
