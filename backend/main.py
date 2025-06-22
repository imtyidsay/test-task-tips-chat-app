from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from auth import router as auth_router

# 環境変数の読み込み
load_dotenv()

# Supabaseクライアントの初期化
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

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
app.include_router(auth_router, prefix="/auth", tags=["auth"])

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress: Optional[int] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    tags: Optional[List[str]] = None

# タスクの取得
@app.get("/tasks")
async def get_tasks():
    try:
        response = supabase.table("tasks").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの作成
@app.post("/tasks")
async def create_task(task: Task):
    try:
        response = supabase.table("tasks").insert(task.dict()).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの更新
@app.put("/tasks/{task_id}")
async def update_task(task_id: str, task: Task):
    try:
        response = supabase.table("tasks").update(task.dict()).eq("id", task_id).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# タスクの削除
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    try:
        response = supabase.table("tasks").delete().eq("id", task_id).execute()
        return {"message": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 