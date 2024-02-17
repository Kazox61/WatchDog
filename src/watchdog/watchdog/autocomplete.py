import coc
import discord
from pathlib import Path
import motor.motor_asyncio

from shared.config import Config


config = Config()

db_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb)

locations = {'global': 'global'}
path = Path().joinpath("assets", "locations.csv")
with open(path, 'r', encoding='utf-8') as f:
    for line in f.readlines():
        line = line.replace('"', '')
        loc, location_id = line.split(',')
        locations[loc] = location_id


async def search_location(ctx: discord.AutocompleteContext):
    return [location for location in locations.keys() if location.lower().startswith(ctx.value.lower())]


async def search_player(ctx: discord.AutocompleteContext):
    search_input = ""
    if ctx.value is not None:
        search_input = ctx.value
        if search_input.startswith("#"):
            search_input = coc.utils.correct_tag(search_input)
    cursor = db_client.WatchDog.players.find(
        {"$or": [{"name": {"$regex": search_input, "$options": "i"}},
                 {"tag": {"$regex": "^" + search_input, "$options": "i"}}]},
        {"name": 1, "tag": 1, "_id": 0}
    ).limit(25)
    result = await cursor.to_list(25)
    players = []
    for document in result:
        players.append(document["name"] + " | " + document["tag"])
    return players


def parse_player(search: str) -> str:
    if ' | #' in search:
        player_tag = search.split(' | ')[1]
    else:
        player_tag = search
    return coc.utils.correct_tag(player_tag)


async def search_group(ctx: discord.AutocompleteContext):
    search_input = ""
    if ctx.value is not None:
        search_input = ctx.value
    cursor = db_client.WatchDog.groups.find({"name": {"$regex": "^" + search_input, "$options": "i"}},
                                            {"name": 1, "owner_name": 1, "_id": 0}
                                            ).limit(25).sort("search_count", -1)
    result = await cursor.to_list(25)
    groups = []
    for document in result:
        groups.append(document["name"])
    return groups


async def parse_group(search: str) -> str:
    group = await db_client.WatchDog.groups.find_one({"name": search})
    if group:
        group["id"] = str(group["_id"])
    return group


async def search_group_user(ctx: discord.AutocompleteContext):
    search_input = ""
    if ctx.value is not None:
        search_input = ctx.value
    cursor = db_client.WatchDog.groups.find(
        {"$and": [
            {"name": {"$regex": "^" + search_input, "$options": "i"}},
            {"members": ctx.interaction.user.id}
        ]},
        {"name": 1, "_id": 0}
    ).limit(25).sort("search_count", -1)
    result = await cursor.to_list(25)
    groups = []
    for document in result:
        groups.append(document["name"])
    return groups


async def parse_group_user(search: str, discord_id: int):
    group = await db_client.WatchDog.groups.find_one({"name": search})
    if group is None:
        return None
    if discord_id not in group["members"]:
        return None
    group["id"] = str(group["_id"])
    return group
