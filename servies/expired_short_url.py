import aioredis
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.redis import sys_cache
from loguru import logger
from aioredis import Redis
from dependencies.base import get_db_session
from servies.short import ShortService


# 处理已经过期的短链
# async 定义异步函数
async def handle_expired_short_tag(redis: Redis, channel, data):
    '''
    处理过期的 short_tag
    '''
    short_tag = str(data)
    logger.info(f"处理过期的 short_tag: {short_tag}")

    # 使用 async for 来处理异步生成器
    async for db_session in get_db_session():
        try:
            # 调用 ShortService 的 delete_short_url 方法来删除过期的 short_url
            result = await ShortService.delete_short_url(db_session, short_tag)
            logger.info(result["message"])
            break  # 成功执行后退出循环
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing request")
            logger.error(f"处理过程中发生异常: {e}")
            # 如果有必要，可以在这里添加更多的错误处理逻辑
        finally:
            # 确保会话被关闭
            await db_session.close()
    logger.info(f"已删除过期的 short_url: {short_tag}, 数据库删除")


# 监听过期短链的redis记录
# 定义异步函数expired_event_listener，用于监听待过期事件
async def expired_event_listener():
    # 获取redis连接
    redis = await sys_cache()
    # 创建pubsub对象
    pubsub = redis.pubsub()
    try:
        # 订阅__keyevent@0__:expired事件
        await pubsub.subscribe("__keyevent@0__:expired")
        logger.info("订阅成功，开始监听待过期事件")
        # 无限循环，等待消息
        while True:  # 显式的无限循环，更清晰地表示意图
            # 获取消息
            message = await pubsub.get_message(ignore_subscribe_messages=False, timeout=10)
            if message:
                logger.info(f"接收到消息: {message}")
                if message['type'] == 'message':
                    logger.info("处理过期事件消息")
                    logger.info(f"message['channel']: {message['channel']}, message['data']: {message['data']}")
                    # 处理过期事件
                    await handle_expired_short_tag(redis, message['channel'], message['data'])
                # else:
                #     logger.info(f"非过期事件消息: {message['type']}")
    except Exception as e:
        logger.error(f"监听过程中发生异常: {e}")
    finally:
        logger.info("正在取消订阅并关闭连接")
        # 取消订阅
        await pubsub.unsubscribe("__keyevent@0__:expired")
        # 关闭redis连接
        await redis.close()
        logger.info("资源已释放")
