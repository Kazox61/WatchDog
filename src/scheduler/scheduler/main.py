import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from pytz import utc
import coc
import asyncio
import motor.motor_asyncio

from shared.coc_utils import get_current_insertion_date
from shared.config import Config

from scheduler import logger

config = Config
db_client = motor.motor_asyncio.AsyncIOMotorClient(
    config.mongodb)

coc_client = coc.Client(key_names="WatchDog", key_count=10)
asyncio.get_event_loop().run_until_complete(coc_client.login(
    config.coc_api_mail+"@gmail.com",
    config.coc_api_password
))

scheduler = AsyncIOScheduler(timezone=utc)
scheduler.start()
logger.debug("Scheduler started successfully.")


async def get_leaderboards() -> tuple[list, list]:
    tasks = []
    tracked_locations = await db_client.watchdog.leaderboards.distinct("location")
    try:
        all_locations = await coc_client.search_locations()
    except coc.Maintenance:
        return
    locations = []
    for location in all_locations:
        if location.name in tracked_locations:
            locations.append(location.name)
            task = asyncio.ensure_future(
                coc_client.get_location_players(location_id=location.id))
            tasks.append(task)
    if 'global' in tracked_locations:
        global_task = asyncio.ensure_future(coc_client.get_location_players())
        tasks.append(global_task)
        locations.append("global")
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return locations, responses


@scheduler.scheduled_job("cron", hour=5, minute=0)
async def new_day_start():
    start_time = time.time()
    date = get_current_insertion_date()
    await db_client.watchdog.players.update_many({}, [{
        "$addFields": {
            "battle_log": {
                date: {
                    "attacks": [],
                    "defenses": [],
                    "reset_trophies": "$trophies"
                }
            }
        }
    }])
    logger.debug(
        f"Created new Legend day for every player in {time.time() - start_time} seconds.")


@scheduler.scheduled_job("cron", hour=5, minute=0)
async def store_all_leaderboards():
    start_time = time.time()
    await db_client.watchdog.leaderboards.update_many(
        {}, {'$set': {'leaderboard': []}})
    locations, leaderboards = await get_leaderboards()
    for index, leaderboard in enumerate(leaderboards):
        location = locations[index]
        documents = []
        for player in leaderboard:
            documents.append({'tag': player.tag, 'name': player.name,
                             'trophies': player.trophies, 'rank': player.rank})
        await db_client.watchdog.leaderboards.update_one(
            {'location': location}, {'$set': {'leaderboard': documents}})
    logger.debug(
        f"All leaderboards stored in {time.time() - start_time} seconds.")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_forever()
