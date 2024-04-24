from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from database.database import SessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


from contextlib import asynccontextmanager
@asynccontextmanager
async def get_db_session_asynccont() -> AsyncGenerator:
    async_session = SessionLocal()
    try:
        yield async_session
        await async_session.commit()
    except SQLAlchemyError as e:
        await async_session.rollback()
        raise e
    finally:
        await async_session.close()
        