from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import sqlite3
import uuid
from auth_sqlite import router as auth_router
from database import init_database, create_admin_user, get_db_connection

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 認証ルーターの追加
app.include_router(auth_router, tags=["auth"])

# タスクのモデル定義
class Task(BaseModel):
    id: Optional[str] = None
    title: str
    status: str
    assignee: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    work_level: Optional[str] = None
    completed: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    progress: Optional[int] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    tags: Optional[str] = None

# タスクの取得
@app.get("/tasks")
async def get_tasks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        tasks_data = cursor.fetchall()
        conn.close()
        
        tasks = []
        for task_data in tasks_data:
            tasks.append({
                "id": task_data["id"],
                "title": task_data["title"],
                "status": task_data["status"],
                "assignee": task_data["assignee"],
                "description": task_data["description"],
                "due_date": task_data["due_date"],
                "priority": task_data["priority"],
                "category": task_data["category"],
                "work_level": task_data["work_level"],
                "completed": bool(task_data["completed"]),
                "created_at": task_data["created_at"],
                "updated_at": task_data["updated_at"],
                "progress": task_data["progress"],
                "estimated_hours": task_data["estimated_hours"],
                "actual_hours": task_data["actual_hours"],
                "tags": task_data["tags"]
            })
        
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの作成
@app.post("/tasks")
async def create_task(task: Task):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        task_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO tasks (id, title, status, assignee, description, due_date, priority, category, work_level, completed, progress, estimated_hours, actual_hours, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id, task.title, task.status, task.assignee, task.description,
            task.due_date, task.priority, task.category, task.work_level,
            task.completed, task.progress, task.estimated_hours, task.actual_hours, task.tags
        ))
        
        conn.commit()
        
        # 作成されたタスクを取得
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        created_task = cursor.fetchone()
        conn.close()
        
        return {
            "id": created_task["id"],
            "title": created_task["title"],
            "status": created_task["status"],
            "assignee": created_task["assignee"],
            "description": created_task["description"],
            "due_date": created_task["due_date"],
            "priority": created_task["priority"],
            "category": created_task["category"],
            "work_level": created_task["work_level"],
            "completed": bool(created_task["completed"]),
            "created_at": created_task["created_at"],
            "updated_at": created_task["updated_at"],
            "progress": created_task["progress"],
            "estimated_hours": created_task["estimated_hours"],
            "actual_hours": created_task["actual_hours"],
            "tags": created_task["tags"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの更新
@app.put("/tasks/{task_id}")
async def update_task(task_id: str, task: Task):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET 
                title = ?, status = ?, assignee = ?, description = ?, due_date = ?,
                priority = ?, category = ?, work_level = ?, completed = ?, progress = ?,
                estimated_hours = ?, actual_hours = ?, tags = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            task.title, task.status, task.assignee, task.description, task.due_date,
            task.priority, task.category, task.work_level, task.completed, task.progress,
            task.estimated_hours, task.actual_hours, task.tags, task_id
        ))
        
        conn.commit()
        
        # 更新されたタスクを取得
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_task = cursor.fetchone()
        conn.close()
        
        if not updated_task:
            raise HTTPException(status_code=404, detail="タスクが見つかりません")
        
        return {
            "id": updated_task["id"],
            "title": updated_task["title"],
            "status": updated_task["status"],
            "assignee": updated_task["assignee"],
            "description": updated_task["description"],
            "due_date": updated_task["due_date"],
            "priority": updated_task["priority"],
            "category": updated_task["category"],
            "work_level": updated_task["work_level"],
            "completed": bool(updated_task["completed"]),
            "created_at": updated_task["created_at"],
            "updated_at": updated_task["updated_at"],
            "progress": updated_task["progress"],
            "estimated_hours": updated_task["estimated_hours"],
            "actual_hours": updated_task["actual_hours"],
            "tags": updated_task["tags"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの削除
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

# データベース初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション開始時にデータベースを初期化"""
    init_database()
    create_admin_user()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 