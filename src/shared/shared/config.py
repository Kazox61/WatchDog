from os import getenv

from dotenv import load_dotenv


load_dotenv(override=True)


class Config:
    server_ip = getenv("SERVER_IP")
    mongodb = f'mongodb://{getenv("MONGO_INITDB_ROOT_USERNAME")}:{getenv("MONGO_INITDB_ROOT_PASSWORD")}@{server_ip}:{getenv("MONGO_PORT")}/WatchDog?authSource={getenv("MONGO_INITDB_ROOT_USERNAME")}'

    redis_port = getenv("REDIS_PORT")

    coc_api_mail = getenv("COC_API_MAIL")
    coc_api_password = getenv("COC_API_PASSWORD")

    discord_token = getenv("DISCORD_TOKEN")
    server_join_channel_id = int(getenv("SERVER_JOIN_CHANNEL_ID"))
    introduction_channel_id = int(getenv("INTRODUCTION_CHANNEL_ID"))

    extensions = [
        "watchdog.cogs.discord_events",
        "watchdog.cogs.general",
        "watchdog.cogs.liveticker",
        "watchdog.cogs.notifications",
        "watchdog.cogs.autoupdate",
        "watchdog.cogs.player",
        "watchdog.cogs.leaderboard",
        "watchdog.cogs.group",
    ]
