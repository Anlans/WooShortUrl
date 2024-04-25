from fastapi import APIRouter, Depends, BackgroundTasks, status, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.base import get_db_session
from models.model import ShortUrl
from servies.short import ShortService
from api.user import oauth2_scheme
from utils.random_helper import generate_short_url_with_base64, generate_short_url
from schemas.base import SingleShortUrlCreate
from utils.auth_helper import AuthTokenHelper
from database.redis import sys_cache
from datetime import datetime, timedelta
from loguru import logger

router_short = APIRouter(tags=["短链操作"])

# 单个长链转短链
@router_short.post("/create/single/short_url", summary="创建单个短链")
async def create_single_short_url(create_info: SingleShortUrlCreate,
                                  token: str = Depends(oauth2_scheme),  # 可以拿到用户登陆的jwt-token
                                  db_session: AsyncSession = Depends(get_db_session)):  # 数据库会话 db_session，用来执行数据库操作
    try:
        payload = AuthTokenHelper.token_decode(token)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="会话过期，请重新登陆")

    username = payload.get("username")

    create_info.short_tag = generate_short_url()
    # count_obj = await db_session.execute(select(func.count()).select_from(ShortUrl))  # 获得目前short_url数据库记录数用作唯一整数
    # count = count_obj.scalars().first()
    # logger.info(f"sql_count: {count.scalars().first()}")
    # create_info.short_tag = generate_short_url_with_base64(count)
    # redis同时绑定过期时间
    await ShortService.set_key_with_expiration(create_info.short_tag, create_info.long_url)

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


# 重定向跳转后的长链接
@router_short.get("/{short_tag}", status_code=status.HTTP_307_TEMPORARY_REDIRECT, summary="根据tag重定向长链")
async def short_redirect(*, short_tag: str,
                         db_session: AsyncSession = Depends(get_db_session),
                         task: BackgroundTasks):
    data = await ShortService.get_short_url(db_session, short_tag)
    if not data:
        raise PlainTextResponse("没有对应的短链信息记录")
    data.visits_count += 1
    task.add_task(ShortService.update_short_url, db_session, short_url_id=data.id, visits_count=data.visits_count)
    return RedirectResponse(url=data.long_url)




