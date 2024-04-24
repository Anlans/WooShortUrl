from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from config.config import get_settings

# 创建引擎对象
async_engine = create_async_engine(get_settings().ASYNC_DATABASE_URL, echo=True)

# 创建模型基类
Base = declarative_base()

# 创建异步的会话对象
SessionLocal = sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)
