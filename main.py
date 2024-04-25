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


# async def handle_expired_short_tag(redis: Redis, channel, data):
#     short_tag = str(data)
#     logger.info(f"处理过期的 short_tag: {short_tag}")
#
#     # 使用 async for 来处理异步生成器
#     async for db_session in get_db_session():
#         try:
#             result = await ShortService.delete_short_url(db_session, short_tag)
#             logger.info(result["message"])
#             break  # 成功执行后退出循环
#         except Exception as e:
#             logger.error(f"处理过程中发生异常: {e}")
#             # 如果有必要，可以在这里添加更多的错误处理逻辑
#         finally:
#             # 确保会话被关闭
#             await db_session.close()
#     logger.info(f"已删除过期的 short_url: {short_tag}, 数据库删除")
#
# async def expired_event_listener():
#     redis = await sys_cache()
#     pubsub = redis.pubsub()
#     try:
#         await pubsub.subscribe("__keyevent@0__:expired")
#         logger.info("订阅成功，开始监听过期事件")
#         while True:  # 显式的无限循环，更清晰地表示意图
#             message = await pubsub.get_message(ignore_subscribe_messages=False, timeout=10)
#             if message:
#                 logger.info(f"接收到消息: {message}")
#                 logger.info(f"message['channel']: {message['channel']}, message['data']: {message['data']}")
#                 if message['type'] == 'message':
#                     logger.info("处理过期事件消息")
#                     logger.info(f"message['channel']: {message['channel']}, message['data']: {message['data']}")
#                     await handle_expired_short_tag(redis, message['channel'], message['data'])
#                 else:
#                     logger.info("没有接收到消息，轮询继续")
#     except Exception as e:
#         logger.error(f"监听过程中发生异常: {e}")
#     finally:
#         logger.info("正在取消订阅并关闭连接")
#         await pubsub.unsubscribe("__keyevent@0__:expired")
#         await redis.close()
#         logger.info("资源已释放")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=2345)
