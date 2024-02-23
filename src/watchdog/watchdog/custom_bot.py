from abc import ABC
import discord
from discord.ext import commands
import motor.motor_asyncio
import asyncio
import coc
from redis import asyncio as redis
import pendulum
import traceback
import ssl
import ujson
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from shared.config import Config
from shared.coc_utils import get_current_insertion_date

from watchdog import logger
from watchdog.emojis import Emojis


class CustomBot(commands.Bot, ABC):
    def __init__(self, config: Config, scheduler: AsyncIOScheduler):
        super().__init__(command_prefix=",",
                         case_insensitive=True,
                         intents=discord.Intents.default(),
                         help_command=None,
                         activity=discord.Game('/info'),
                         # debug_guilds=[1121860500972642324]
                         )
        self.start_time = pendulum.now(pendulum.UTC)

        self.config = config
        self.scheduler = scheduler

        self.db_client = motor.motor_asyncio.AsyncIOMotorClient(
            self.config.mongodb)
        self.player_db = self.db_client.WatchDog.players
        self.user_db = self.db_client.WatchDog.users
        self.leaderboard_db = self.db_client.WatchDog.leaderboards
        self.group_db = self.db_client.WatchDog.groups

        self.coc_client = coc.Client(key_names="WatchDog", key_count=10)
        asyncio.get_event_loop().run_until_complete(self.coc_client.login(
            config.coc_api_mail+"@gmail.com",
            config.coc_api_password
        ))

        self.redis = redis.Redis(host=self.config.server_ip, port=self.config.redis_port, password=self.config.redis_password,
                                 retry_on_timeout=True, retry_on_error=[redis.ConnectionError])

        self.emoji = Emojis()
        self.number_emojis = [self.emoji.number_0, self.emoji.number_1, self.emoji.number_2, self.emoji.number_3, self.emoji.number_4,
                              self.emoji.number_5, self.emoji.number_6, self.emoji.number_7, self.emoji.number_8, self.emoji.number_9]

    async def on_ready(self):
        logger.debug(f'Bot is logged in as {self.user} ID: {self.user.id}')

    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ) -> None:
        if isinstance(error, discord.ApplicationCommandInvokeError):
            error = error.original
        if isinstance(error, coc.errors.Maintenance):
            await ctx.respond('The clash of clans api currently is in maintenance. Please try again later.')
            return
        elif isinstance(error, asyncio.exceptions.TimeoutError) or isinstance(error, ssl.SSLCertVerificationError):
            await ctx.respond('It seems like the clash of clans api has some problems. Please try again later.')
            return
        await ctx.respond('Ooops, something went wrong. I informed my developer so he can fix it.')
        exc = ctx.command.qualified_name
        exc += ' caused the following error:\n'
        exc += ''.join(traceback.format_exception(type(error),
                       error, error.__traceback__, chain=True))
        logger.error(exc)

    def get_number_emoji(self, number: int):
        if 0 <= number <= 9:
            return self.number_emojis[number]
        else:
            raise ValueError("Number is not between 0 and 9.")

    def get_discord_commands(self) -> dict:
        discord_commands = {}
        for name, cog in self.cogs.items():
            for command in cog.get_commands():
                collected_commands = self.collect_commands(command.to_dict())
                if collected_commands == []:
                    continue
                discord_commands[name] = collected_commands
        return discord_commands

    def collect_commands(self, command: dict = None, current_command_name: str = "", discord_commands: list = None):
        if discord_commands is None:
            discord_commands = []
        if "options" not in command:
            return discord_commands
        current_command_name += command["name"] + " "
        add_command = False
        for option in command["options"]:
            if "options" in option:
                discord_commands = self.collect_commands(option,
                                                         current_command_name,
                                                         discord_commands)
            else:
                add_command = True
                break
        if add_command:
            params = []
            for option in command["options"]:
                params.append(option["name"])
            discord_commands.append({
                "name": current_command_name.strip(),
                "description": command["description"],
                "params": params
            })
        return discord_commands

    async def try_create_user(self, discord_id: int):
        result = await self.user_db.find_one({'discord_id': discord_id})
        if result:
            return False
        self.user_db.insert_one(
            {'discord_id': discord_id})
        return True

    async def try_create_player(self, player_tag) -> bool:
        count = await self.player_db.count_documents({'tag': player_tag})
        if count > 0:
            return False
        try:
            player = await self.coc_client.get_player(player_tag)
        except coc.NotFound:
            return False
        except coc.Maintenance:
            return False
        await self.player_db.insert_one(
            {'tag': player.tag, 'name': player.name, 'trophies': player.trophies, 'attack_wins': player.attack_wins,
             'defense_wins': player.defense_wins,
             'battle_log': {get_current_insertion_date(): {'attacks': [], 'defenses': [], 'reset_trophies': player.trophies}}})
        return True

    async def get_player(self, tag: str) -> dict:
        tag = coc.utils.correct_tag(tag)

        try:
            redis_player = await self.redis.get(tag)
        except redis.ConnectionError:
            redis_player = None

        if redis_player is not None:
            return ujson.loads(redis_player)

        player = await self.player_db.find_one({'tag': tag}, {'_id': 0})

        if player is None:
            return None
        try:
            await self.redis.setex(tag, 120, ujson.dumps(player))
        except redis.ConnectionError:
            pass
        return player

    async def get_players(self, tags: list[str]) -> list[dict]:
        players = []
        tag_set = set([coc.utils.correct_tag(tag) for tag in tags])
        try:
            cache_data = await self.redis.mget(keys=list(tag_set))
            for data in cache_data:
                if data is None:
                    continue

                data = ujson.loads(data)
                tag_set.remove(data.get("tag"))
                players.append(data)
        except redis.ConnectionError:
            pass

        tasks = []
        for tag in tag_set:
            task = asyncio.ensure_future(self.get_player(tag))
            tasks.append(task)

        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for response in responses:
                players.append(response)

        return [player for player in players if player is not None]
