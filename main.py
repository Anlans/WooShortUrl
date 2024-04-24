from fastapi import FastAPI, APIRouter
from database.database import async_engine, Base
from dependencies.base import get_db_session
from api.user import router_user
from api.short import router_short


app = FastAPI()


@app.on_event("startup")
async def start_event():
    async def init_create_table():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await init_create_table()


@app.on_event("shutdown")
async def shutdown_event():
    pass


app.include_router(router_user)
app.include_router(router_short)
