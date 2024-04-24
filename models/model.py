from database.database import Base
from sqlalchemy import Column, Integer, String, DateTime, func


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20))
    password = Column(String(20))
    create_at = Column(DateTime(), default=func.now())


class ShortUrl(Base):
    __tablename__ = "short_url"
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_tag = Column(String(20), nullable=False)
    short_url = Column(String(20))
    long_url = Column(String, nullable=False)
    visits_count = Column(Integer, default=0)
    create_at = Column(DateTime(), default=func.now())
    created_by = Column(String(20))
    msg_context = Column(String, nullable=False)

