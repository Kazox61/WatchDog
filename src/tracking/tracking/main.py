import asyncio
from collections import deque
import ujson
from msgspec import Struct
from msgspec.json import decode
import aiohttp
import ujson
from asyncio_throttle import Throttler
from redis import asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uvicorn import Config as uvicorn_Config
from uvicorn import Server
import motor.motor_asyncio
from pymongo import UpdateOne
import zlib

from shared.config import Config
from shared.coc_utils import create_keys, get_current_insertion_date


RATE_LIMIT = 30


config = Config()

cache = redis.Redis(host=config.server_ip, port=config.redis_port, db=1,
                    decode_responses=False, max_connections=5000)

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(config.mongodb)


class Player(Struct):
    tag: str


async def send_ws(ws, json):
    try:
        await ws.send_json(json)
    except:
        pass


async def get_player_responses(keys: deque, tags: list[str]) -> list[bytes]:
    tasks = []
    connector = aiohttp.TCPConnector(limit=2000, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=1800)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for tag in tags:
            keys.rotate(1)

            async def fetch(url: str, session: aiohttp.ClientSession, headers: dict):
                async with session.get(url, headers=headers) as new_response:
                    if new_response.status == 404:  # remove banned players
                        t = url.split("%23")[-1]
                        await mongo_client.WatchDog.players.delete_one({"tag": t})
                        await mongo_client.WatchDog.groups.update_many({}, {"$pull": {"players": t}})
                        return None
                    elif new_response.status != 200:
                        return None
                    new_response = await new_response.read()
                    return new_response
            tasks.append(fetch(url=f'https://api.clashofclans.com/v1/players/{tag.replace("#", "%23")}', session=session, headers={
                         "Authorization": f"Bearer {keys[0]}"}))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        await session.close()
    return results


async def update_player(new_response: bytes, previous_compressed_response: bytes, bulk_changes: list, ws_tasks: list, clients: list):
    obj = decode(new_response, type=Player)
    compressed_new_response = zlib.compress(new_response)

    if compressed_new_response == previous_compressed_response:
        return

    tag = obj.tag

    await cache.set(tag, compressed_new_response, ex=300)

    if previous_compressed_response is None:
        return None

    current_date = get_current_insertion_date()

    new_response = ujson.loads(new_response)

    previous_uncompressed_response = zlib.decompress(
        previous_compressed_response)
    previous_response = ujson.loads(previous_uncompressed_response)

    diff_trophies = new_response["trophies"] - previous_response["trophies"]
    diff_attack_wins = new_response["attackWins"] - \
        previous_response["attackWins"]
    diff_defense_wins = new_response["defenseWins"] - \
        previous_response["defenseWins"]
    not_changed = diff_trophies == 0 and diff_defense_wins == 0 and diff_attack_wins == 0
    league = new_response.get("league", {}).get("name", "Unranked")

    if new_response["name"] != previous_response["name"]:
        bulk_changes.append(UpdateOne({"tag": tag},
                                      {"$set": {"name": new_response["name"]}}))

    if not_changed:
        return

    if new_response["trophies"] < 4900 and league != "Legend League":
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$set': {'trophies': new_response["trophies"]}}))
        return

    got_zero_star_defense = diff_trophies == 0 and diff_defense_wins > 0
    if got_zero_star_defense:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$push': {f'battle_log.{current_date}.defenses': 0}}))

    gained_trophies = diff_trophies > 0
    if gained_trophies:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$push': {f'battle_log.{current_date}.attacks': diff_trophies}}))

    lost_trophies = diff_trophies < 0 and diff_attack_wins == 0
    if lost_trophies:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$push': {f'battle_log.{current_date}.defenses': diff_trophies}}))

    sync_hits = diff_trophies < 0 and diff_attack_wins > 0
    if sync_hits:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$push': {f'battle_log.{current_date}.defenses': diff_trophies}}))

    if diff_trophies != 0:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$set': {'trophies': new_response["trophies"]}}))

    if diff_attack_wins > 0:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$set': {'attack_wins': new_response["attackWins"]}}))

    if diff_defense_wins > 0:
        bulk_changes.append(UpdateOne({'tag': tag},
                                      {'$set': {'defense_wins': new_response["defenseWins"]}}))

    changes = {"type": "diffTrophies",
               "tag": tag,
               "diffTrophies": diff_trophies}
    for ws in clients:
        ws_tasks.append(send_ws(ws=ws, json=changes))


async def main(keys: deque, clients: list):
    player_collection = mongo_client.WatchDog.players
    await cache.flushdb()

    loop_throttler = Throttler(rate_limit=1, period=30)
    while True:
        async with loop_throttler:
            tags = await player_collection.distinct("tag")
            max_tag_split = len(keys) * RATE_LIMIT
            split_tags = [tags[i:i + max_tag_split]
                          for i in range(0, len(tags), max_tag_split)]

            bulk_changes = []
            ws_tasks = []

            key_throttler = Throttler(rate_limit=1, period=1)
            for tag_group in split_tags:
                async with key_throttler:
                    responses = await get_player_responses(keys=keys, tags=tag_group)
                    cache_results = await cache.mget(keys=tag_group)
                    response_tasks = [update_player(new_response=response, previous_compressed_response=cache_results[count], bulk_changes=bulk_changes, ws_tasks=ws_tasks, clients=clients)
                                      for count, response in enumerate(responses) if isinstance(response, bytes)]
                    await asyncio.gather(*response_tasks)

            if bulk_changes != []:
                results = await player_collection.bulk_write(bulk_changes)

            if ws_tasks != []:
                await asyncio.gather(*ws_tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    app = FastAPI()
    clients = set()

    @app.websocket("/players")
    async def player_websocket(websocket: WebSocket):
        await websocket.accept()
        clients.add(websocket)
        try:
            while True:
                data = await websocket.receive_text()
        except WebSocketDisconnect:
            clients.remove(websocket)

    uvicorn_config = uvicorn_Config(app=app, loop="asyncio",
                                    host="0.0.0.0", port=6002)
    server = Server(uvicorn_config)

    keys = create_keys()
    loop.create_task(server.serve())
    loop.create_task(main(deque(keys), clients))
    loop.run_forever()
