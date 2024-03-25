from pydantic import BaseModel


class User(BaseModel):
    discord_id: str
    avatar: str
    access_token: str
    refresh_token: str
