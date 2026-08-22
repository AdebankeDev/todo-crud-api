from fastapi import FastAPI, HTTPException, status, Header, Depends, Response, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from pydantic import ValidationError
import os

import psycopg
from dotenv import load_dotenv
from supabase_client import supabase
from fastapi.responses import JSONResponse
from auth import get_current_user
from llm.schema import ResumeExtractRequest, ResumeExtractResponse
from llm.client import (
    extract_resume,
    parse_json,
    validate_output,
    repair_llm_output,
    quarantine_failure,
)


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


app = FastAPI(
    title="Task API",
    description="A simple in-memory CRUD API for managing tasks.",
    version="1.0.0"
)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    field = exc.errors()[0]["loc"][-1]

    return JSONResponse(
        status_code=400,
        content={
            "error": f"Invalid field: {field}"
        }
    )

# DATABASE IMPLEMENTATION
connection = psycopg.connect(DATABASE_URL)
connection.autocommit = True

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL
)
""")

# To get the number of rows in table tasks

cursor.execute("SELECT COUNT(*) FROM tasks")
count = cursor.fetchone()[0]

if count == 0:
    sample_tasks = [
        ("Learn FastAPI", False),
        ("Build CRUD API", False),
        ("Push project to GitHub", True),
    ]

    cursor.executemany(
        "INSERT INTO tasks (title, done) VALUES (%s, %s)",
        sample_tasks
    )



class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

class SignupRequest(BaseModel):
    email: str
    password: str


@app.get(
    "/",
    summary="API Information",
    description="Returns basic information about the Task API."
)
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get(
    "/health",
    summary="Health Check",
    description="Checks the health of the API."
)
def health():
    return {
        "status": "ok"
    }


@app.get(
    "/tasks",
    summary="Get all tasks",
    description="Returns a list of all tasks."
)
def get_tasks():
    cursor.execute("SELECT * FROM tasks ORDER BY id")
    rows = cursor.fetchall()

    tasks = []

    for row in rows:
        task = {
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        }
        tasks.append(task)
    
    return tasks

    


@app.get(
    "/tasks/{task_id}",
    summary="Get a task",
    description="Returns a single task by its ID."
)
def get_task(task_id: int):
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    task = {
        "id": row[0],
        "title": row[1],
        "done": bool(row[2])
    }

    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task."
)
def create_task(task: TaskCreate):
    if task.title.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title is required and cannot be empty"
        )

    cursor.execute(
    """
    INSERT INTO tasks (title, done)
    VALUES (%s, %s)
    RETURNING id
    """,
    (task.title, False)
)
    new_id = cursor.fetchone()[0]

    new_task = {
        "id": new_id,
        "title": task.title,
        "done": False
    }

    return new_task


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates the title and completion status of a task."
)
def update_task(task_id: int, updated_task: TaskUpdate):
    
    if updated_task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    cursor.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s",
                   (updated_task.title, updated_task.done, task_id))
    

    if cursor.rowcount == 0:
        raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )        
    return {
        "id": task_id,
        "title": updated_task.title,
        "done": updated_task.done
    }
    
                           

@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Deletes a task by its ID."
)
def delete_task(task_id: int):

    cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

# Task Statistics Endpoint
@app.get(
    "/stats",
    summary="Task statistics",
    description="Returns statistics about all tasks."
)
def get_stats():

    total = cursor.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

    done = cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]

    open_tasks = total - done

    return {
        "total": total,
        "done": done,
        "open": open_tasks
    }


# Authentication Endpoints
@app.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED
    )
def signup(request: SignupRequest):
    
    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    try:
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )
        return response.user.model_dump()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    


# Authentication Endpoints
@app.post("/auth/login")
def login(request: SignupRequest):

    if not request.email or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials"
        )

# Public route that does not require authentication
@app.get("/public/info")
def public_info():
        return {
            "message": "Welcome stranger! This info is public."
        }


# Protected route that requires authentication
@app.get("/protected/profile")
def get_profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


# Protected route that requires authentication
@app.get("/protected/dashboard")
def dashboard(user=Depends(get_current_user)):
    return {
        "message": f"Welcome {user.email}",
        "user_id": user.id
    }



# Authentication Endpoints
@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    supabase.auth.sign_out()
    return Response(status_code=204)


# Resume Extraction Endpoint
@app.post(
    "/extract",
    summary="Extract structured information from a resume"
)
def extract_resume_endpoint(request: ResumeExtractRequest):

    if os.getenv("LLM_STUB") == "1":
        return ResumeExtractResponse(
            name="Ada Lovelace",
            email="ada@example.com",
            phone="+1234567890",
            skills=["Python", "FastAPI"],
            education="Computer Engineering",
            experience_years=2.0,
            confidence=0.95,
            needs_review=False
        )

    raw_output = extract_resume(request.text)

    try:
        parsed_output = parse_json(raw_output)
        validated_output = validate_output(parsed_output)

        return validated_output

    except (ValueError, ValidationError) as first_error:

        try:
            repaired_output = repair_llm_output(
                request.text,
                raw_output,
                str(first_error),
            )

            parsed_repaired = parse_json(repaired_output)
            validated_repaired = validate_output(parsed_repaired)

            return validated_repaired

        except (ValueError, ValidationError) as second_error:

            quarantine_failure(
                input_text=request.text,
                raw_output=raw_output,
                repaired_output=repaired_output,
                error=str(second_error),
            )

            raise HTTPException(
                status_code=422,
                detail="LLM output could not be parsed or validated after one repair attempt.",
            )
