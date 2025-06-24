from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
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

# セキュリティ設定
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")  # 本番環境では必ず環境変数から取得
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# モデル定義
class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserInDB(User):
    password_hash: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class Admin(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    role: str = "admin"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ユーティリティ関数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
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
    
    # Supabaseからユーザー情報を取得
    try:
        response = supabase.table("users").select("*").eq("email", token_data.email).execute()
        user = response.data[0] if response.data else None
        if user is None:
            raise credentials_exception
        return User(**user)
    except Exception as e:
        raise credentials_exception

async def get_current_admin(token: str = Depends(oauth2_scheme)) -> Admin:
    credentials_exception = HTTPException(
        status_code=401,
        detail="管理者認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # JWTトークンにrole情報がない場合は、データベースから確認
    if role != "admin":
        # usersテーブルから管理者ロールのユーザーを検索
        try:
            user_response = supabase.table("users").select("*").eq("email", token_data.email).eq("role", "admin").eq("is_active", True).execute()
            user = user_response.data[0] if user_response.data else None
            
            if not user:
                raise credentials_exception
        except Exception as e:
            raise credentials_exception
    
    # まずSupabaseのadminsテーブルから管理者情報を取得
    try:
        admin_response = supabase.table("admins").select("*").eq("email", token_data.email).eq("is_active", True).execute()
        admin = admin_response.data[0] if admin_response.data else None
        
        if admin:
            return Admin(**admin)
        
        # adminsテーブルにない場合、usersテーブルから管理者ロールのユーザーを検索
        user_response = supabase.table("users").select("*").eq("email", token_data.email).eq("role", "admin").eq("is_active", True).execute()
        user = user_response.data[0] if user_response.data else None
        
        if user:
            # usersテーブルのデータをAdminモデルに変換
            admin_data = {
                "id": user.get("id"),
                "email": user.get("email"),
                "name": user.get("name", ""),
                "role": user.get("role", "admin"),
                "is_active": user.get("is_active", True),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            }
            return Admin(**admin_data)
        
        raise credentials_exception
    except Exception as e:
        raise credentials_exception

# ルーターの設定
router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(user_data: UserRegister):
    try:
        # パスワードのハッシュ化
        password_hash = get_password_hash(user_data.password)
        
        # ユーザーの作成
        user_record = {
            "email": user_data.email,
            "password_hash": password_hash,
            "name": user_data.name or "ユーザー",
            "role": "user",
            "is_active": True
        }
        
        response = supabase.table("users").insert(user_record).execute()
        return User(**response.data[0])
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="ユーザーの登録に失敗しました"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # ユーザーの検証
        response = supabase.table("users").select("*").eq("email", form_data.username).execute()
        user = response.data[0] if response.data else None

        # password_hashフィールドを使用（hashed_passwordではなく）
        password_hash = user.get("password_hash") if user else None
        
        if not user or not password_hash or not verify_password(form_data.password, password_hash):
            raise HTTPException(
                status_code=401,
                detail="メールアドレスまたはパスワードが正しくありません",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # アクセストークンの作成（ユーザーのロールを含める）
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {"sub": user["email"]}
        
        # 管理者ロールの場合は、トークンにrole情報を追加
        if user.get("role") == "admin":
            token_data["role"] = "admin"
        
        access_token = create_access_token(
            data=token_data, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="認証に失敗しました",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/admin/me", response_model=Admin)
async def read_admin_me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin

@router.get("/admin/users")
async def get_all_users(current_admin: Admin = Depends(get_current_admin)):
    try:
        response = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="ユーザー一覧の取得に失敗しました"
        )

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user 