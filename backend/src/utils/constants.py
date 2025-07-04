# backend/src/utils/constants.py
# Define user roles and other constants

from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    HEAD_TEACHER = "head_teacher" # 부장선생님
    HOMEROOM_TEACHER = "homeroom_teacher" # 담임선생님
    STUDENT = "student"
