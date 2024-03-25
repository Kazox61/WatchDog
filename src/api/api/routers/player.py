from fastapi import APIRouter, HTTPException
from datetime import timedelta, datetime

from api.models import TrackedPlayer, BasicPlayer
from api.dependencies import DbDep

router = APIRouter(prefix="/player", tags=["Player Endpoints"])


def get_insertion_date(date: datetime) -> str:
    d = date.date() if (date.hour >= 5) or (
        date.hour == 4 and date.minute > 58) else date.date() - timedelta(days=1)
    return d.strftime("%Y") + d.strftime("%m") + d.strftime("%d")


def get_current_insertion_date() -> str:
    now = datetime.utcnow()
    return get_insertion_date(now)


@router.get("/{player_tag}", response_model=TrackedPlayer | None, summary="Get Player")
async def get_player(player_tag: str, db: DbDep):
    if player_tag.startswith("%23"):
        player_tag.replace("%23", "#")
    player_result = await db.WatchDog.players.find_one({"tag": player_tag}, {"_id": 0})
    if player_result is None:
        raise HTTPException(404, "Player not found")
    day = player_result["battle_log"][get_current_insertion_date()]
    return TrackedPlayer(
        name=player_result["name"],
        tag=player_result["tag"],
        trophies=player_result["trophies"],
        start_trophies=day["reset_trophies"],
        attacks=day["attacks"],
        defenses=day["defenses"])


@router.get("/{player_tag}/days", summary="Get Player Days")
async def get_player_days(player_tag: str, db: DbDep):
    player_tag.replace("%23", "#")
    player_result = await db.WatchDog.players.find_one({"tag": player_tag}, {"_id": 0})
    if player_result is None:
        raise HTTPException(404, "Player not found")
    return player_result["battle_log"]


@router.get("/search/{search_str}", summary="Get Player Names")
async def get_player_search(search_str: str, db: DbDep):
    search_str = search_str[1:]
    cursor = db.WatchDog.players.find(
        {"$or": [{"name": {"$regex": search_str, "$options": "i"}},
                 {"tag": {"$regex": "^" + search_str, "$options": "i"}}]},
        {"tag": 1, "name": 1, "_id": 0}
    )
    result = await cursor.to_list(25)
    players = {}
    for document in result:
        players[document["tag"]] = document["name"]
    return players
