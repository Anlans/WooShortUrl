from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.model import User
from dependencies.base import get_db_session

class UserService:
    @staticmethod
    async def create_user(async_session: AsyncSession, **kwargs):
        new_user = User(**kwargs)
        async_session.add(new_user)
        await async_session.commit()
        return new_user

    @staticmethod
    async def get_user_by_name(async_session: AsyncSession, username: str):
        result = await async_session.execute(select(User).where(User.username == username))
        return result.scalars().first()
