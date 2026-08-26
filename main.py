from fastapi import FastAPI, HTTPException, Response, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from auth import get_current_user
from supabase_client import supabase
from repositories.task_repository import TaskRepository


load_dotenv()


app = FastAPI(
    title="Task Auth API",
    version="1.0"
)

repository = TaskRepository()


# =========================
# Request Models
# =========================

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


class AuthRequest(BaseModel):
    email: str
    password: str


# =========================
# Root Endpoint
# =========================

@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task Auth API",
        "version": "1.0",
        "endpoints": [
            "/tasks",
            "/auth/signup",
            "/auth/login"
        ]
    }


# =========================
# Authentication
# =========================

@app.post("/auth/signup", status_code=201)
def signup(auth: AuthRequest):

    if not auth.email.strip() or not auth.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_up({
            "email": auth.email,
            "password": auth.password
        })

        print("SUPABASE SIGNUP RESPONSE:", response)

        if response.user is None:
            raise HTTPException(
                status_code=400,
                detail="Unable to create user"
            )

        return {
            "user": response.user
        }

    except HTTPException:
        raise

    except Exception as e:
        print("SUPABASE SIGNUP ERROR:", repr(e))

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/auth/login")
def login(auth: AuthRequest):

    if not auth.email.strip() or not auth.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": auth.email,
            "password": auth.password
        })

        if response.session is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid login credentials"
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials"
        )


# =========================
# Tasks
# =========================

@app.get("/tasks", summary="Get all tasks")
def get_tasks():
    return repository.get_all()


@app.get("/tasks/{task_id}", summary="Get a task by ID")
def get_task(task_id: int):

    task = repository.get_by_id(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    return repository.create(task.title)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    existing = repository.get_by_id(task_id)

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    updated = repository.update(
        task_id,
        task.title,
        task.done
    )

    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):

    deleted = repository.delete(task_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return Response(status_code=204)

# =========================
# Public & Protected Routes
# =========================

@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }

@app.get("/protected/profile")
def protected_profile(current_user=Depends(get_current_user)):

    user = current_user["user"]

    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@app.get("/protected/dashboard")
def protected_dashboard(current_user=Depends(get_current_user)):

    user = current_user["user"]

    return {
        "message": "Welcome to your protected dashboard",
        "user_id": user.id,
        "email": user.email
    }

@app.post("/auth/logout", status_code=204)
def logout(current_user=Depends(get_current_user)):

    try:
        supabase.auth.sign_out()

        return Response(status_code=204)

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Unable to logout"
        )