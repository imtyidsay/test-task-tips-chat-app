import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from passlib.context import CryptContext

# 環境変数の読み込み
load_dotenv()

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    """データベース接続を取得"""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD")
        )
        return connection
    except Exception as e:
        print(f"データベース接続エラー: {str(e)}")
        return None

def execute_sql_file(connection, sql_content):
    """SQLを実行"""
    try:
        cursor = connection.cursor()
        cursor.execute(sql_content)
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"SQL実行エラー: {str(e)}")
        connection.rollback()
        return False

def create_tables_and_policies():
    """テーブルとポリシーを作成"""
    connection = get_db_connection()
    if not connection:
        return False

    # DDLとポリシーのSQL
    sql_content = """
    -- 管理者テーブル
    CREATE TABLE IF NOT EXISTS admins (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'admin',
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- ユーザーテーブル（auth.pyと一致するフィールド名）
    CREATE TABLE IF NOT EXISTS users (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        disabled BOOLEAN DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- タスクテーブル
    CREATE TABLE IF NOT EXISTS tasks (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT '未着手',
        assignee TEXT NOT NULL,
        description TEXT,
        due_date DATE,
        priority TEXT,
        category TEXT,
        work_level TEXT,
        completed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        progress INTEGER DEFAULT 0,
        estimated_hours INTEGER,
        actual_hours INTEGER,
        tags TEXT[]
    );

    -- updated_atを自動更新する関数の作成
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- updated_atの自動更新トリガーの作成
    DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
    CREATE TRIGGER update_tasks_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- RLSの有効化
    ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
    ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

    -- 管理者テーブルのポリシー
    DROP POLICY IF EXISTS "Admins can view all admins" ON admins;
    CREATE POLICY "Admins can view all admins" ON admins
        FOR SELECT USING (auth.role() = 'authenticated');

    DROP POLICY IF EXISTS "Admins can insert admins" ON admins;
    CREATE POLICY "Admins can insert admins" ON admins
        FOR INSERT WITH CHECK (auth.role() = 'authenticated');

    -- ユーザーテーブルのポリシー
    DROP POLICY IF EXISTS "Users can view their own data" ON users;
    CREATE POLICY "Users can view their own data" ON users
        FOR SELECT USING (auth.uid() = id);

    DROP POLICY IF EXISTS "Admins can view all users" ON users;
    CREATE POLICY "Admins can view all users" ON users
        FOR SELECT USING (auth.role() = 'authenticated');

    -- タスクテーブルのポリシー
    DROP POLICY IF EXISTS "Enable read access for all users" ON tasks;
    CREATE POLICY "Enable read access for all users" ON tasks
        FOR SELECT USING (true);

    DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON tasks;
    CREATE POLICY "Enable insert for authenticated users only" ON tasks
        FOR INSERT WITH CHECK (auth.role() = 'authenticated');

    DROP POLICY IF EXISTS "Enable update for authenticated users only" ON tasks;
    CREATE POLICY "Enable update for authenticated users only" ON tasks
        FOR UPDATE USING (auth.role() = 'authenticated');

    DROP POLICY IF EXISTS "Enable delete for authenticated users only" ON tasks;
    CREATE POLICY "Enable delete for authenticated users only" ON tasks
        FOR DELETE USING (auth.role() = 'authenticated');
    """

    success = execute_sql_file(connection, sql_content)
    connection.close()
    
    if success:
        print("テーブルとポリシーの作成が完了しました")
    return success

def insert_initial_data():
    """初期データを挿入"""
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        
        # 管理者データの挿入
        admin_data = {
            "email": "admin@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK8i",
            "name": "管理者",
            "role": "admin"
        }
        
        cursor.execute("""
            INSERT INTO admins (email, password_hash, name, role) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (admin_data["email"], admin_data["password_hash"], admin_data["name"], admin_data["role"]))
        
        # サンプルユーザーデータの挿入（パスワード: password123）
        sample_users = [
            ("user1@example.com", pwd_context.hash("password123"), "ユーザー1", False),
            ("user2@example.com", pwd_context.hash("password123"), "ユーザー2", False)
        ]
        
        for user_data in sample_users:
            cursor.execute("""
                INSERT INTO users (email, hashed_password, full_name, disabled) 
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, user_data)
        
        # サンプルタスクデータの挿入
        sample_tasks = [
            (
                "新規事業公募　Socket事業計画作成",
                "未着手",
                "寺園亮",
                "Socket事業の計画書を作成し、公募に応募する",
                (datetime.now() + timedelta(days=30)).date(),
                "中",
                "企画",
                "大",
                False,
                0,
                4,
                0,
                ["重要"]
            ),
            (
                "荒木和美先生　LOOKREC手続きメール送付",
                "未着手",
                "寺園亮",
                "荒木和美先生にLOOKREC手続きについてのメールを送付する",
                (datetime.now() + timedelta(days=7)).date(),
                "高",
                "メール",
                "小",
                False,
                0,
                1,
                0,
                ["重要"]
            )
        ]
        
        for task_data in sample_tasks:
            cursor.execute("""
                INSERT INTO tasks (title, status, assignee, description, due_date, priority, category, work_level, completed, progress, estimated_hours, actual_hours, tags) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, task_data)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("初期データの挿入が完了しました")
        return True
        
    except Exception as e:
        print(f"初期データ挿入エラー: {str(e)}")
        connection.rollback()
        connection.close()
        return False

def main():
    """メイン関数"""
    print("PostgreSQL直接接続によるデータベース初期化を開始します...")
    
    # テーブルとポリシーの作成
    if create_tables_and_policies():
        # 初期データの挿入
        insert_initial_data()
    
    print("データベース初期化が完了しました")

if __name__ == "__main__":
    main() 