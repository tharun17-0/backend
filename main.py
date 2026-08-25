from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase_client import supabase

from repositories.task_repository import TaskRepository

load_dotenv()

app = FastAPI()

repository = TaskRepository()

app = FastAPI(
    title="Task Auth API",
    version="1.0"
)

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


# Root endpoint
@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


# GET all tasks
@app.get("/tasks", summary="Get all tasks")
def get_tasks():
    return repository.get_all()


# GET one task
@app.get("/tasks/{task_id}", summary="Get a task by ID")
def get_task(task_id: int):

    task = repository.get_by_id(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


# POST - create a task
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    return repository.create(task.title)


# PUT - update a task
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


# DELETE - delete a task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):

    deleted = repository.delete(task_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return Response(status_code=204)