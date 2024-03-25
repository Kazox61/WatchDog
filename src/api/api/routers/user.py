from fastapi import Request, Response, APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from os import getenv
import aiohttp
import jwt
import datetime

from api.dependencies import LoginDep
from api.models.user import User

router = APIRouter(prefix="/user", tags=["Discord Endpoints"])
jwt_algorithm = "HS256"
jwt_secret = getenv("JWT_SECRET")
oauth2_url = getenv("OAUTH2_URL")


@router.get("/", response_model=User)
async def get_user(user: LoginDep):
    print(user)
    return user


@router.get("/logout")
async def get_user_logout(response: Response):
    response.delete_cookie("_session", path="/")
    response.status_code = 200
    return response


@router.get("/login")
async def get_user_login():
    return RedirectResponse(url=oauth2_url)


@router.get("/login/redirect")
async def get_user_login_redirect(code: str):
    data = aiohttp.FormData()
    data.add_field(name="client_id", value=getenv("CLIENT_ID"))
    data.add_field(name="client_secret", value=getenv("CLIENT_SECRET"))
    data.add_field(name="grant_type", value="authorization_code")
    data.add_field(name="code", value=code)
    data.add_field(name="redirect_uri",
                   value="http://localhost:8000/user/login/redirect")

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url="https://discord.com/api/v10/oauth2/token", data=data, headers=headers) as response:
            res = await response.json()
            access_token = res["access_token"]

            headers = {"Authorization": f"Bearer {access_token}"}

            async with session.get(url="https://discord.com/api/v10/users/@me", headers=headers) as response:
                userinfo = await response.json()

                # ?size=? 16-4096
                # avatar_url = f"https://cdn.discordapp.com/avatars/{userinfo['id']}/{userinfo['avatar']}.png"
                response = RedirectResponse(url="http://localhost:5173/")
                payload = {
                    "discordId": userinfo['id'],
                    "avatar": userinfo['avatar'],
                    "accessToken": res["access_token"],
                    "refreshToken": res["refresh_token"],
                }
                cookie = jwt.encode(
                    payload=payload, key=jwt_secret, algorithm=jwt_algorithm)
                response.set_cookie(key="_session", value=cookie, expires=(datetime.datetime.now(
                ) + datetime.timedelta(days=60)).astimezone(tz=datetime.timezone.utc))
                return response
