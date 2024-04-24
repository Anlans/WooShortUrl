from jose import jwt, JWTError
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError


SECRET_KEY = "la3rwLn7VA%A9v*NC^$FX5J5QtW^T!B4"
ALGORITHM = "HS256"

class AuthTokenHelper:

    @staticmethod
    def token_encode(data):
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def token_decode(token):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except (JWTError, ValidationError):
            raise credentials_exception
