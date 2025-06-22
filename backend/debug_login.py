from supabase import create_client, Client
import os
from dotenv import load_dotenv
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

def debug_login():
    """ログイン問題をデバッグ"""
    try:
        print("=== ログインデバッグ開始 ===")
        
        # 1. ユーザーデータの確認
        print("\n1. データベース内のユーザーデータ:")
        response = supabase.table("users").select("*").execute()
        
        if response.data:
            for user in response.data:
                print(f"  - Email: {user.get('email')}")
                print(f"    Name: {user.get('name', 'N/A')}")
                print(f"    Full Name: {user.get('full_name', 'N/A')}")
                print(f"    Password Hash: {user.get('password_hash', 'N/A')[:20]}...")
                print(f"    Hashed Password: {user.get('hashed_password', 'N/A')[:20] if user.get('hashed_password') else 'N/A'}...")
                print(f"    Role: {user.get('role', 'N/A')}")
                print(f"    Is Active: {user.get('is_active', 'N/A')}")
                print()
        else:
            print("  ユーザーデータが見つかりません")
        
        # 2. パスワード検証テスト
        print("\n2. パスワード検証テスト:")
        test_password = "password123"
        test_hash = pwd_context.hash(test_password)
        print(f"  テストパスワード: {test_password}")
        print(f"  生成されたハッシュ: {test_hash}")
        
        # 3. user1のデータを詳細確認
        print("\n3. user1@example.comの詳細確認:")
        user1_response = supabase.table("users").select("*").eq("email", "user1@example.com").execute()
        
        if user1_response.data:
            user1 = user1_response.data[0]
            print(f"  見つかったユーザー: {user1}")
            
            # パスワード検証
            password_hash = user1.get('password_hash') or user1.get('hashed_password')
            if password_hash:
                is_valid = pwd_context.verify(test_password, password_hash)
                print(f"  パスワード検証結果: {is_valid}")
            else:
                print("  パスワードハッシュが見つかりません")
        else:
            print("  user1@example.comが見つかりません")
        
        # 4. 新しいユーザーを作成してテスト
        print("\n4. 新しいテストユーザーの作成:")
        new_user_data = {
            "email": "testuser@example.com",
            "password_hash": pwd_context.hash("password123"),
            "name": "テストユーザー",
            "role": "user",
            "is_active": True
        }
        
        try:
            insert_response = supabase.table("users").insert(new_user_data).execute()
            print(f"  新しいユーザーを作成しました: {insert_response.data[0] if insert_response.data else '失敗'}")
        except Exception as e:
            print(f"  ユーザー作成エラー: {str(e)}")
        
    except Exception as e:
        print(f"デバッグ中にエラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    debug_login()

if __name__ == "__main__":
    main() 