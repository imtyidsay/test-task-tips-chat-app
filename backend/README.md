# タスク管理アプリケーション バックエンド

## 技術スタック
- Python 3.8+
- FastAPI
- Supabase
- Uvicorn

## セットアップ手順

1. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

2. 環境変数の設定
`.env.example`を`.env`にコピーし、必要な環境変数を設定します：
```bash
cp .env.example .env
```

以下の環境変数を設定してください：
- `SUPABASE_URL`: SupabaseのプロジェクトURL
- `SUPABASE_KEY`: Supabaseの匿名キー
- `JWT_SECRET`: JWTの署名に使用する秘密鍵

3. アプリケーションの起動
```bash
uvicorn main:app --reload
```

## APIエンドポイント

### タスク管理
- `GET /tasks`: すべてのタスクを取得
- `POST /tasks`: 新しいタスクを作成
- `PUT /tasks/{task_id}`: タスクを更新
- `DELETE /tasks/{task_id}`: タスクを削除

## Supabaseのテーブル構造

### users テーブル
| カラム名 | 型 | 説明 |
|----------|------|------------|
| id | uuid | 主キー（自動生成） |
| email | text | ユーザーのメールアドレス（一意） |
| name | text | ユーザー名 |
| password_hash | text | ハッシュ化されたパスワード |
| role | text | ユーザーの役割（デフォルト: "user"） |
| is_active | boolean | アクティブ状態（デフォルト: true） |
| created_at | timestamp | 作成日時（自動設定） |
| updated_at | timestamp | 更新日時（自動更新） |

### admins テーブル
| カラム名 | 型 | 説明 |
|----------|------|------------|
| id | uuid | 主キー（自動生成） |
| email | text | 管理者のメールアドレス（一意） |
| name | text | 管理者名 |
| role | text | 管理者の役割（デフォルト: "admin"） |
| is_active | boolean | アクティブ状態（デフォルト: true） |
| created_at | timestamp | 作成日時（自動設定） |
| updated_at | timestamp | 更新日時（自動更新） |

### tasks テーブル
| カラム名 | 型 | 説明 |
|----------|------|------------|
| id | uuid | 主キー |
| title | text | タスクのタイトル |
| status | text | タスクの状態（未着手/進行中/完了） |
| assignee | text | 担当者 |
| description | text | タスクの説明 |
| due_date | date | 期限日 |
| priority | text | 優先度（高/中/低） |
| category | text | カテゴリ |
| work_level | text | 作業量（小/中/大） |
| completed | boolean | 完了フラグ |
| created_at | timestamp | 作成日時 |
| updated_at | timestamp | 更新日時 |
| progress | integer | 進捗率（0-100） |
| estimated_hours | integer | 見積時間 |
| actual_hours | integer | 実績時間 |
| tags | text[] | タグの配列 |

## 認証・認可

### サンプルユーザー
- **ユーザー1**: `user1@example.com` / `password123`
- **ユーザー2**: `user2@example.com` / `password123`
- **管理者**: `admin@example.com` / `admin123`

### 認証エンドポイント
- `POST /auth/register`: ユーザー登録
- `POST /auth/token`: ユーザーログイン（OAuth2形式）
- `POST /auth/admin/login`: 管理者ログイン
- `GET /auth/users/me`: 現在のユーザー情報取得
- `GET /auth/admin/me`: 現在の管理者情報取得
- `GET /auth/admin/users`: 全ユーザー一覧取得（管理者のみ） 