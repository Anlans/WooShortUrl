import os
import aioredis


async def sys_cache() -> aioredis.Redis:
    """
    短链缓存
    :return: cache 连接池
    """
    redis_url = f"redis://{os.getenv('CACHE_HOST', '127.0.0.1')}:{os.getenv('CACHE_PORT', 6379)}"
    return await aioredis.from_url(
        redis_url,
        db=int(os.getenv('CACHE_DB', 0)),
        encoding='utf-8',
        decode_responses=True
    )
