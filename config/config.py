from pydantic import BaseModel
from functools import lru_cache


class Settings(BaseModel):
    ASYNC_DATABASE_URL: str = "sqlite+aiosqlite:///short.db"


@lru_cache()
def get_settings():
    return Settings()
