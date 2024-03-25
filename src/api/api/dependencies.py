from typing import Annotated
from fastapi import Depends, Request, HTTPException
import jwt
from os import getenv
import motor.motor_asyncio

from shared.config import Config
from api.models import User

config = Config()

jwt_algorithm = "HS256"
jwt_secret = getenv("JWT_SECRET")


async def get_db():
    db_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb)
    try:
        yield db_client
    finally:
        db_client.close()

DbDep = Annotated[motor.motor_asyncio.AsyncIOMotorClient, Depends(get_db)]


async def handle_login(request: Request) -> User:
    if "_session" not in request.cookies:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        discord_user = jwt.decode(
            request.cookies["_session"], jwt_secret, algorithms=[jwt_algorithm])
        return User(discord_id=discord_user["discordId"],
                    avatar=discord_user["avatar"],
                    access_token=discord_user["accessToken"],
                    refresh_token=discord_user["refreshToken"])
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="User not authenticated")
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="User not authenticated")

LoginDep = Annotated[User, Depends(handle_login)]
