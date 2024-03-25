from pydantic import BaseModel
from typing import Annotated


class TrackedPlayer(BaseModel):
    name: str
    tag: str
    trophies: int
    start_trophies: int
    attacks: list[int]
    defenses: list[int]


class BasicPlayer(BaseModel):
    tag: str
    name: str
