import sqlite3
import os
from passlib.context import CryptContext
from datetime import datetime

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_PATH = "database.db"

def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
    return conn

def init_database():
    """データベースとテーブルを初期化"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # usersテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # tasksテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT DEFAULT '未着手',
            assignee TEXT NOT NULL,
            description TEXT,
            due_date TEXT,
            priority TEXT,
            category TEXT,
            work_level TEXT,
            completed BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            tags TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def create_admin_user():
    """管理者ユーザーを作成"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 既存の管理者をチェック
    cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@example.com",))
    existing_admin = cursor.fetchone()
    
    if not existing_admin:
        # 管理者を作成
        admin_id = "admin-001"
        password_hash = pwd_context.hash("admin123")
        
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, "admin@example.com", password_hash, "管理者", "admin", 1))
        
        print("管理者アカウントを作成しました: admin@example.com / admin123")
    else:
        print("管理者アカウントは既に存在します")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    create_admin_user()
    print("データベースの初期化が完了しました") 