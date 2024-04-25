from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func
from datetime import datetime, timedelta
from dependencies.base import get_db_session, get_db_session_asynccont
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from servies.user import UserService
from servies.short import ShortService
from utils.passlib_helper import PasslibHelper
from utils.auth_helper import AuthTokenHelper


router_user = APIRouter(prefix="/api/v1", tags=["用户管理接口"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/oauth2/authorize")


class UserCreate(BaseModel):
    username: str
    password: str
    create_at: datetime = datetime.now()


@router_user.post("/create_user", summary="创建用户")
async def create_user(user: UserCreate):
    async with get_db_session_asynccont() as async_session:
        await UserService.create_user(async_session,
                                      username=user.username,
                                      password=PasslibHelper.hash_password(user.password),
                                      create_at=user.create_at)
@router_user.post("/oauth2/authorize", summary="jwt-token")
async def login(user_data: OAuth2PasswordRequestForm = Depends(),
                db_session: AsyncSession = Depends(get_db_session)):

    if not user_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入用户名及密码")

    # 查询用户存在否
    user_info = await UserService.get_user_by_name(db_session, user_data.username)
    if not user_info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="不存在该用户", headers={"WWW-Authenticate": "Basic"})

    # verify用户密码
    if not PasslibHelper.verify_password(user_data.password, user_info.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户密码不对")

    data = {
        'iss': user_info.username,
        'sub': 'admin',
        'username': user_info.username,
        'admin': True,
        'exp': datetime.utcnow() + timedelta(hours=2)
    }

    # 生成token
    token = AuthTokenHelper.token_encode(data=data)

    return {"access_token": token, "token_type": "bearer"}





