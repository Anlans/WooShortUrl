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
            expired_at = int(timedelta(days=3).total_seconds())
            await redis.set(key, value, ex=expired_at)
            logger.info(f"Key {key} set with expiration of {expired_at} seconds.")
        except Exception as e:
            logger.error(f"Failed to set key in Redis: {str(e)}")
