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
from utils.random_helper import generate_short_url
from schemas.base import SingleShortUrlCreate


router_user = APIRouter(prefix="/api/v1", tags=["用户创建短链管理接口"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/oauth2/authorize")


class UserCreate(BaseModel):
    username: str
    password: str
    create_at: datetime = datetime.now()


@router_user.post("/create_user")
async def create_user(user: UserCreate):
    async with get_db_session_asynccont() as async_session:
        await UserService.create_user(async_session,
                                      username=user.username,
                                      password=PasslibHelper.hash_password(user.password),
                                      create_at=user.create_at)
@router_user.post("/oauth2/authorize")
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
        'exp': datetime.utcnow() + timedelta(minutes=29)
    }

    # 生成token
    token = AuthTokenHelper.token_encode(data=data)

    return {"access_token": token, "token_type": "bearer"}


# 单个长链转短链
@router_user.post("/create/single/short_url")
async def create_single_short_url(create_info: SingleShortUrlCreate,
                                  token: str = Depends(oauth2_scheme),  # 可以拿到用户登陆的jwt-token
                                  db_session: AsyncSession = Depends(get_db_session)):  # 数据库会话 db_session，用来执行数据库操作
    try:
        payload = AuthTokenHelper.token_decode(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="会话过期，请重新登陆")

    username = payload.get("username")
    create_info.short_tag = generate_short_url()
    create_info.short_url = f"{create_info.short_url}{create_info.short_tag}"
    create_info.created_by = username
    if not (create_info.long_url.startswith("http://") or create_info.long_url.startswith("https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="长链接需以'https://'或'http://'开头")
    create_info.msg_context = f"{create_info.msg_context}, 了解详情请点击{create_info.short_url}"

    result = await ShortService.create_short_url(db_session, **create_info.dict())
    return {
        "status_code": 100,
        "msg": "短链创建成功",
        "data": {
            "short_url": result.short_url
        }
    }



