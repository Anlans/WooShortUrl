import aioredis
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from dependencies.base import get_db_session
from models.model import User, ShortUrl
from fastapi.responses import RedirectResponse, PlainTextResponse
from database.redis import sys_cache
from loguru import logger
from aioredis import Redis

class ShortService:
    @staticmethod
    async def create_short_url(async_session: AsyncSession, **kwargs):
        new_short_url = ShortUrl(**kwargs)
        async_session.add(new_short_url)
        await async_session.commit()
        return new_short_url

    # @staticmethod
    # async def create_custom_short_url(async_session: AsyncSession, **kwargs):
    #     new_short_url = ShortUrl(**kwargs)
    #     async_session.add(new_short_url)
    #     await async_session.commit()
    #     return new_short_url

    @staticmethod
    async def get_short_url(async_session: AsyncSession, short_tag: str):
        result = await async_session.execute(select(ShortUrl).where(ShortUrl.short_tag == short_tag))
        return result.scalars().first()

    @staticmethod
    async def update_short_url(async_session: AsyncSession, short_url_id: int, **kwargs):
        response = update(ShortUrl).where(ShortUrl.id == short_url_id)
        result = await async_session.execute(response.values(**kwargs))
        await async_session.commit()
        return result

    # 添加删除短链的功能，用以配合长时间短链不使用则废弃
    @staticmethod
    async def delete_short_url(async_session: AsyncSession, short_tag: str):
        result = await async_session.execute(select(ShortUrl).where(ShortUrl.short_tag == short_tag))
        delete_short_url = result.scalars().first()
        if delete_short_url is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据库中无该短链记录")
        await async_session.delete(delete_short_url)
        await async_session.commit()
        # 返回成功删除的消息
        return {"message": "Short TAG deleted successfully", "short_tag": short_tag}

    # 检测3天不用的短链
    @staticmethod
    async def set_key_with_expiration(key, value="exists"):
        try:
            redis = await sys_cache()
            expired_at = int(timedelta(days=1).total_seconds())
            await redis.set(key, value, ex=expired_at)
            logger.info(f"Key {key} set with expiration of {expired_at} seconds.")
        except Exception as e:
            logger.error(f"Failed to set key in Redis: {str(e)}")

    @staticmethod
    async def verify_custom_short_url(async_session: AsyncSession, tag: str) -> bool:
        # 使用提供的标签来查询数据库
        result = await async_session.execute(select(ShortUrl).where(ShortUrl.short_tag == tag))
        # 提取查询结果的第一条记录
        short_url_instance = result.scalars().first()
        logger.info(f"short_url_instance: {short_url_instance}")
        # 如果查询结果为空，则返回 False（标签不存在，可用）
        # 如果查询结果不为空，则返回 True（标签已存在，不可用）
        return short_url_instance is not None

    @staticmethod
    async def get_all_short_url_page(async_session: AsyncSession,
                                     last_seen_id: int,
                                     page_size: int) -> dict:
        if last_seen_id is not None:
            query = select(ShortUrl).where(ShortUrl.id > last_seen_id).order_by(ShortUrl.id).limit(page_size)
        else:
            query = select(ShortUrl).order_by(ShortUrl.id).limit(page_size)

        result = await async_session.execute(query)
        if not result:
            raise PlainTextResponse("在short表中一条记录都没有查询到")
        items = result.scalars().all()

        next_last_seen_id = items[-1].id if items else None

        return {
            "items": items,
            "next_last_seen_id": next_last_seen_id
        }



