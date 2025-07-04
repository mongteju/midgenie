# Jeju High School Admission Backend

This is the backend for the Jeju High School Admission web application.

## Features

*   **User Authentication & Authorization**:
    *   Admin-only user registration and role management.
    *   Role-based access control (Admin, Head Teacher, Homeroom Teacher, Student).
*   **School Management**: CRUD operations for high school information.
*   **Student Management**: CRUD operations for student information, with homeroom teacher assignment.
*   **Grade Management**:
    *   Head Teacher can upload grade files (CSV/XLSX).
    *   View student grades (Admin, Head Teacher, Homeroom Teacher for their students, Student for their own grades).
*   **Student Application Management**:
    *   Homeroom Teacher can manage student high school applications (select school, mark acceptance).
    *   View student application status (Admin, Head Teacher, Homeroom Teacher for their students, Student for their own application).

## Technologies

*   **Framework**: FastAPI
*   **Database**: SQLAlchemy (with SQLite for development, configurable for others)
*   **Authentication**: JWT (JSON Web Tokens)
*   **Password Hashing**: `passlib`
*   **Environment Variables**: `python-dotenv`

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd jejudo-highschool-project/backend
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment**:
    *   **Windows**:
        ```bash
        .venv\Scripts\activate
        ```
    *   **macOS/Linux**:
        ```bash
        source .venv/bin/activate
        ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure environment variables**:
    Create a `.env` file in the `backend/` directory based on `.env.example`.
    ```
    DATABASE_URL="sqlite:///./test.db"
    SECRET_KEY="your-super-secret-key-here"
    ```
    **IMPORTANT**: Change `SECRET_KEY` to a strong, random string for production.

6.  **Run database migrations** (if using a real database, you'd set up Alembic or similar):
    For SQLite, the database file (`test.db`) will be created automatically on first run if it doesn't exist. You'll need to set up initial data (e.g., an admin user) manually or via a script.

7.  **Run the application**:
    ```bash
    uvicorn src.app:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the server is running, you can access the interactive API documentation (Swagger UI) at:
`http://127.0.0.1:8000/docs`

## Project Structure

```
backend/
├───src/
│   ├───app.py              # Main application entry point
│   ├───config.py           # Environment variable loading and basic configuration
│   ├───database/           # Database related files
│   │   ├───models.py       # Database model definitions (SQLAlchemy)
│   │   └───schemas.py      # Data validation and serialization/deserialization schemas (Pydantic)
│   ├───routes/             # API endpoint definitions (resource-specific)
│   │   ├───auth.py         # Authentication routes
│   │   ├───schools.py      # School routes
│   │   ├───students.py     # Student routes
│   │   ├───grades.py       # Grade routes
│   │   └───applications.py # Student application routes
│   ├───services/           # Business logic implementation
│   │   ├───auth_service.py
│   │   ├───school_service.py
│   │   ├───student_service.py
│   │   ├───grade_service.py
│   │   └───application_service.py
│   └───utils/              # Common utility functions and helpers
│       ├───constants.py    # User role definitions and other constants
│       ├───helpers.py
│       └───auth_decorators.py # Role-based access control decorators
├───tests/                  # Unit and integration tests
│   ├───test_auth.py
│   ├───test_schools.py
│   ├───test_students.py
│   ├───test_grades.py
│   └───test_applications.py
├───.env.example            # Example environment variables
├───.gitignore              # Git version control ignore file
├───requirements.txt        # Python dependencies
└───README.md               # Project documentation
```

## Contributing

Please follow the existing code style and conventions.
