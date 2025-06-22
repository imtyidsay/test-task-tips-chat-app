from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from passlib.context import CryptContext

# 環境変数の読み込み
load_dotenv()

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Supabaseクライアントの初期化
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def insert_initial_data():
    """初期データを挿入する"""
    try:
        # 管理者用の初期データ（パスワード: admin123）
        admin_data = {
            "email": "admin@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i",
            "name": "管理者",
            "role": "admin"
        }
        
        # 既存データをチェックしてから挿入
        existing_admin = supabase.table("admins").select("*").eq("email", admin_data["email"]).execute()
        if not existing_admin.data:
            supabase.table("admins").insert(admin_data).execute()
            print("管理者データを挿入しました")
        else:
            print("管理者データは既に存在します")

        # サンプルユーザーデータ（パスワード: password123）
        sample_users = [
            {
                "email": "user1@example.com",
                "password_hash": pwd_context.hash("password123"),
                "name": "ユーザー1",
                "is_active": True
            },
            {
                "email": "user2@example.com",
                "password_hash": pwd_context.hash("password123"),
                "name": "ユーザー2",
                "is_active": True
            }
        ]

        for user_data in sample_users:
            existing_user = supabase.table("users").select("*").eq("email", user_data["email"]).execute()
            if not existing_user.data:
                supabase.table("users").insert(user_data).execute()
                print(f"ユーザー '{user_data['name']}' を追加しました")
            else:
                print(f"ユーザー '{user_data['name']}' は既に存在します")

    except Exception as e:
        print(f"初期データ挿入でエラーが発生しました: {str(e)}")

def insert_sample_tasks():
    """サンプルタスクデータを挿入する"""
    try:
        # サンプルデータの挿入
        sample_tasks = [
            {
                "title": "新規事業公募　Socket事業計画作成",
                "status": "未着手",
                "assignee": "寺園亮",
                "description": "Socket事業の計画書を作成し、公募に応募する",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "priority": "中",
                "category": "企画",
                "work_level": "大",
                "completed": False,
                "progress": 0,
                "estimated_hours": 4,
                "actual_hours": 0,
                "tags": ["重要"]
            },
            {
                "title": "荒木和美先生　LOOKREC手続きメール送付",
                "status": "未着手",
                "assignee": "寺園亮",
                "description": "荒木和美先生にLOOKREC手続きについてのメールを送付する",
                "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                "priority": "高",
                "category": "メール",
                "work_level": "小",
                "completed": False,
                "progress": 0,
                "estimated_hours": 1,
                "actual_hours": 0,
                "tags": ["重要"]
            }
        ]

        for task in sample_tasks:
            # 既存データをチェック
            existing_task = supabase.table("tasks").select("*").eq("title", task["title"]).execute()
            if not existing_task.data:
                supabase.table("tasks").insert(task).execute()
                print(f"タスク '{task['title']}' を追加しました")
            else:
                print(f"タスク '{task['title']}' は既に存在します")

    except Exception as e:
        print(f"サンプルタスク挿入でエラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    print("初期データの挿入を開始します...")
    insert_initial_data()
    insert_sample_tasks()
    print("初期データの挿入が完了しました")

if __name__ == "__main__":
    main() 