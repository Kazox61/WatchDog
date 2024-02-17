from datetime import datetime, timedelta
import coc
import aiohttp
from base64 import b64decode as base64_b64decode
import json
import asyncio
import coc

from shared.config import Config

config = Config()

SUPER_SCRIPTS = ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]


def get_season_days() -> list[str]:
    start_date = coc.utils.get_season_start()
    end_date = datetime.utcnow()

    season_days = []
    current_date = start_date
    while current_date <= end_date:
        key = get_insertion_date(current_date)
        season_days.append(key)
        current_date += timedelta(days=1)
    return season_days


def get_current_insertion_date() -> str:
    now = datetime.utcnow()
    return get_insertion_date(now)


def get_insertion_date(date: datetime) -> str:
    d = date.date() if (date.hour >= 5) or (
        date.hour == 4 and date.minute > 58) else date.date() - timedelta(days=1)
    return d.strftime("%Y") + d.strftime("%m") + d.strftime("%d")


async def get_keys(emails: list, key_names: str, key_count: int):
    keys = []
    for email in emails:
        coc_client = coc.Client(key_names=key_names, key_count=key_count)
        await coc_client.login(
            email,
            config.coc_api_password
        )
        keys.extend(coc_client.http._keys)
        await coc_client.close()
    return keys


def create_keys():
    coc_api_emails = []
    for i in range(1, 5):
        coc_api_emails.append(f"{config.coc_api_mail}{i}@gmail.com")
    while True:
        try:
            event_loop = asyncio.get_event_loop()
            keys = event_loop.run_until_complete(
                get_keys(emails=coc_api_emails, key_names="test", key_count=10))
            return keys
        except Exception:
            continue
