from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(
    title="Task API",
    description="A simple in-memory CRUD API for managing tasks.",
    version="1.0.0"
)

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

tasks = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "done": False
    },
    {
        "id": 2,
        "title": "Build CRUD API",
        "done": False
    },
    {
        "id": 3,
        "title": "Push project to GitHub",
        "done": True
    }
]


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
def get_tasks(done: bool = None):

    if done is None:
        return tasks

    filtered_tasks = []

    for task in tasks:
        if task["done"] == done:
            filtered_tasks.append(task)

    return filtered_tasks


@app.get(
    "/tasks/{task_id}",
    summary="Get a task",
    description="Returns a single task by its ID."
)
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


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

    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)

    return new_task


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates the title and completion status of a task."
)
def update_task(task_id: int, updated_task: TaskUpdate):

    for task in tasks:

        if task["id"] == task_id:

            if updated_task.title.strip() == "":
                raise HTTPException(
                    status_code=400,
                    detail="Title cannot be empty"
                )

            task["title"] = updated_task.title
            task["done"] = updated_task.done

            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Deletes a task by its ID."
)
def delete_task(task_id: int):

    for task in tasks:

        if task["id"] == task_id:

            tasks.remove(task)

            return

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )


@app.get(
    "/stats",
    summary="Task statistics",
    description="Returns statistics about all tasks."
)
def get_stats():

    total = len(tasks)

    done = sum(1 for task in tasks if task["done"])

    open_tasks = total - done

    return {
        "total": total,
        "done": done,
        "open": open_tasks
    }