from passlib.context import CryptContext
from loguru import logger


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasslibHelper:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
