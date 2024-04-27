import asyncio
from typing import AsyncGenerator

import uvicorn
from aioredis import Redis
from fastapi import FastAPI, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from servies.expired_short_url import expired_event_listener

from database.database import async_engine, Base
from database.redis import sys_cache
from dependencies.base import get_db_session
from api.user import router_user
from api.short import router_short
from models.model import ShortUrl
from loguru import logger

from servies.short import ShortService

app = FastAPI()


@app.on_event("startup")
async def start_event():
    async def init_create_table():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await init_create_table()
    # 启动过期事件监听
    logger.info("启动过期事件监听")
    asyncio.create_task(expired_event_listener())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Starting shutdown process...")
    # 如果有打开的Redis连接，确保它们被关闭
    redis = await sys_cache()
    await redis.close()
    logger.info("Shutdown process completed.")


app.include_router(router_user)
app.include_router(router_short)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=2345)
