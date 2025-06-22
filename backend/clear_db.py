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

def clear_and_recreate_data():
    """既存データを削除して新しいスキーマで再作成"""
    try:
        print("既存データの削除を開始します...")
        
        # 既存のデータを削除
        supabase.table("tasks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("users").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("admins").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        print("既存データの削除が完了しました")
        
        # 新しいデータを挿入
        print("新しいデータの挿入を開始します...")
        
        # 管理者用の初期データ（パスワード: admin123）
        admin_data = {
            "email": "admin@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i",
            "name": "管理者",
            "role": "admin"
        }
        
        supabase.table("admins").insert(admin_data).execute()
        print("管理者データを挿入しました")

        # サンプルユーザーデータ（パスワード: password123）
        sample_users = [
            {
                "email": "user1@example.com",
                "hashed_password": pwd_context.hash("password123"),
                "full_name": "ユーザー1"
            },
            {
                "email": "user2@example.com",
                "hashed_password": pwd_context.hash("password123"),
                "full_name": "ユーザー2"
            }
        ]

        for user_data in sample_users:
            supabase.table("users").insert(user_data).execute()
            print(f"ユーザー '{user_data['full_name']}' を追加しました")

        # サンプルタスクデータの挿入
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
            supabase.table("tasks").insert(task).execute()
            print(f"タスク '{task['title']}' を追加しました")

        print("新しいデータの挿入が完了しました")

    except Exception as e:
        print(f"データの再作成でエラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    print("データベースのクリアと再作成を開始します...")
    clear_and_recreate_data()
    print("データベースのクリアと再作成が完了しました")

if __name__ == "__main__":
    main() 