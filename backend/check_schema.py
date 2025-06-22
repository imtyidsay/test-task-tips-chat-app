from supabase import create_client, Client
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Supabaseクライアントの初期化
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def check_users_schema():
    """usersテーブルのスキーマを確認"""
    try:
        # 既存のユーザーデータを取得してスキーマを確認
        response = supabase.table("users").select("*").limit(1).execute()
        
        if response.data:
            print("usersテーブルの既存データ:")
            for key, value in response.data[0].items():
                print(f"  {key}: {type(value).__name__} = {value}")
        else:
            print("usersテーブルにデータがありません")
            
        # テーブル構造を確認するための空のレコード挿入テスト
        print("\nテーブル構造の確認中...")
        
    except Exception as e:
        print(f"スキーマ確認でエラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    print("usersテーブルのスキーマを確認します...")
    check_users_schema()
    print("スキーマ確認が完了しました")

if __name__ == "__main__":
    main() 