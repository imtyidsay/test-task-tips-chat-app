from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import sqlite3
import uuid

# データベース設定
DATABASE_PATH = "database.db"

# セキュリティ設定
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# モデル定義
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class User(BaseModel):
    id: Optional[str] = None
    email: str
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserInDB(User):
    password_hash: str

class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def verify_password(plain_password, hashed_password):
    """パスワードを検証"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """パスワードをハッシュ化"""
    return pwd_context.hash(password)

def get_user_by_email(email: str):
    """メールアドレスでユーザーを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return UserInDB(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            is_active=bool(user_data["is_active"]),
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"],
            password_hash=user_data["password_hash"]
        )
    return None

def authenticate_user(email: str, password: str):
    """ユーザー認証"""
    user = get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """アクセストークンを作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """現在のユーザーを取得"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)):
    """現在の管理者を取得"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )
    return current_user

# ルーター設定
router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """ログイン（管理者・ユーザー共通）"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(user_data: UserRegister):
    """ユーザー登録"""
    # 既存ユーザーをチェック
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    # 新しいユーザーを作成
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())
    password_hash = get_password_hash(user_data.password)
    
    cursor.execute('''
        INSERT INTO users (id, email, password_hash, name, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_data.email, password_hash, user_data.name or "ユーザー", "user", 1))
    
    conn.commit()
    conn.close()
    
    # 作成されたユーザーを返す
    new_user = get_user_by_email(user_data.email)
    return User(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報を取得"""
    return User(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.get("/admin/me", response_model=User)
async def read_admin_me(current_admin: User = Depends(get_current_admin)):
    """現在の管理者情報を取得"""
    return User(
        id=current_admin.id,
        email=current_admin.email,
        name=current_admin.name,
        role=current_admin.role,
        is_active=current_admin.is_active,
        created_at=current_admin.created_at,
        updated_at=current_admin.updated_at
    )

@router.get("/admin/users")
async def get_all_users(current_admin: User = Depends(get_current_admin)):
    """全ユーザー一覧を取得（管理者用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, name, role, is_active, created_at, updated_at FROM users ORDER BY created_at DESC")
    users_data = cursor.fetchall()
    conn.close()
    
    users = []
    for user_data in users_data:
        users.append({
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data["role"],
            "is_active": bool(user_data["is_active"]),
            "created_at": user_data["created_at"],
            "updated_at": user_data["updated_at"]
        })
    
    return users

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, current_admin: User = Depends(get_current_admin)):
    """ユーザーを削除（管理者用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return {"message": "ユーザーが削除されました"}

@router.patch("/admin/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, current_admin: User = Depends(get_current_admin)):
    """ユーザーの有効/無効を切り替え（管理者用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 現在の状態を取得
    cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    
    # 状態を反転
    new_status = not bool(result["is_active"])
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    conn.commit()
    
    # 更新されたユーザー情報を取得
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()
    
    return {
        "id": updated_user["id"],
        "email": updated_user["email"],
        "name": updated_user["name"],
        "role": updated_user["role"],
        "is_active": bool(updated_user["is_active"]),
        "created_at": updated_user["created_at"],
        "updated_at": updated_user["updated_at"]
    } 