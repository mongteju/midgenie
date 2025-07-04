# backend/src/app.py
# Main application entry point
# Example: FastAPI app instance

from fastapi import FastAPI
from .routes import auth, schools, students, grades, applications

app = FastAPI()

app.include_router(auth.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(applications.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Jeju High School Admission API"}
