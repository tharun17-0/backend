from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db, get_connection

app = FastAPI()
init_db()

tasks = []

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
    connection = get_connection()

    rows = connection.execute(
        "SELECT * FROM tasks"
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


# GET one task
@app.get("/tasks/{task_id}", summary="Get a task by ID")
def get_task(task_id: int):
    connection = get_connection()

    row = connection.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    return dict(row)

# POST - create a task
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if not task.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, 0)
    )

    task_id = cursor.lastrowid

    conn.commit()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return dict(row)

# PUT - update a task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):

    if task.title is None and task.done is None:
        raise HTTPException(
            status_code=400,
            detail="No fields to update"
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    existing = cursor.fetchone()

    if existing is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    new_title = (
        task.title
        if task.title is not None
        else existing["title"]
    )

    new_done = (
        int(task.done)
        if task.done is not None
        else existing["done"]
    )

    if not new_title.strip():
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (new_title, new_done, task_id)
    )

    conn.commit()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    updated = cursor.fetchone()

    conn.close()

    return dict(updated)

# DELETE - delete a task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )

    task = cursor.fetchone()

    if task is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return Response(status_code=204)