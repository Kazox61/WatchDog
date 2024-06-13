import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from bson.objectid import ObjectId
import math

from watchdog.custom_bot import CustomBot
from watchdog.cogs.group import sort_by_current_trophies
from watchdog.components import PlayerTableEmbed, PlayerSimpleEmbed, PlayerOverviewEmbed
from watchdog.background import player_event_emitter
from watchdog import logger
from shared.async_extensions import run_tasks


class AutoUpdate(commands.Cog):
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

        self.bot.scheduler.add_job(self.update_groups, "interval", minutes=5)
        self.bot.scheduler.add_job(
            self.update_leaderboard_current, "interval", minutes=5)
        self.bot.scheduler.add_job(
            self.update_leaderboard_daystart, "cron", hour=5, minute=5)

        player_event_emitter.on(
            "diffTrophies", self.update_player)

    async def update_groups(self):
        update_tasks = []
        async for group in self.bot.group_db.find({"autoupdate": {"$exists": True}}):
            players = await self.bot.get_players(group["players"])
            players.sort(key=sort_by_current_trophies, reverse=True)

            if players == []:
                continue

            embed = PlayerTableEmbed(
                f"Autoupdate {group['name']}", players[:40], 1)
            embed.description += f'Last updated: <t:{str(datetime.now().timestamp()).split(".")[0]}:R>'

            for autoupdate in group["autoupdate"]:
                async def update_group_message(autoupdate: dict, embed: discord.Embed):
                    channel_id = autoupdate["channel_id"]
                    message_id = autoupdate["message_id"]
                    try:
                        await self.bot.http.edit_message(
                            str(channel_id), str(message_id), content="", embeds=[embed.to_dict()])
                    except (discord.NotFound, discord.errors.Forbidden, RuntimeError):
                        await self.bot.group_db.update_one(
                            {"_id": ObjectId(group["_id"])},
                            {"$pull": {
                                "autoupdate": {
                                    "channel_id": channel_id,
                                    "message_id": message_id
                                }
                            }})

                update_tasks.append(update_group_message(autoupdate, embed))

        logger.debug(f"Autoupdate {len(update_tasks)} groups")

        await run_tasks(update_tasks, math.ceil(len(update_tasks) / 40))

    async def update_leaderboard_current(self):
        update_tasks = []
        async for leaderboard in self.bot.leaderboard_db.find({"autoupdate.leaderboard_current": {"$exists": True}}):
            location_id = leaderboard["location_id"]
            location_name = leaderboard["name"]

            if location_id == 'global':
                rank_players = await self.bot.coc_client.get_location_players()
            else:
                rank_players = await self.bot.coc_client.get_location_players(location_id)

            player_tags = [player.tag for player in rank_players]

            db_players = await self.bot.get_players(player_tags)

            players = []
            for rank_player in rank_players:
                player = next(
                    (player for player in db_players if player['tag'] == rank_player.tag), None)

                if player is None:
                    player = {
                        "name": rank_player.name,
                        "trophies": rank_player.trophies
                    }
                players.append(player)

            embed = PlayerTableEmbed(
                f"Autoupdate Leaderboard current {location_name}",
                players[:40], 1)
            embed.description += f'Last updated: <t:{str(datetime.now().timestamp()).split(".")[0]}:R>'

            for autoupdate in leaderboard["autoupdate"]["leaderboard_current"]:
                async def update_leaderboard_message(autoupdate: dict, embed: discord.Embed):
                    channel_id = autoupdate["channel_id"]
                    message_id = autoupdate["message_id"]
                    try:
                        await self.bot.http.edit_message(
                            str(channel_id), str(message_id), content="", embeds=[embed.to_dict()])
                    except (discord.NotFound, discord.errors.Forbidden, RuntimeError):
                        await self.bot.leaderboard_db.update_one(
                            {"location_id": location_id},
                            {"$pull": {
                                "autoupdate.leaderboard_current": {
                                    "channel_id": channel_id,
                                    "message_id": message_id
                                }
                            }})

                update_tasks.append(
                    update_leaderboard_message(autoupdate, embed))

        logger.debug(f"Autoupdate {len(update_tasks)} current leaderboards")

        await run_tasks(update_tasks, math.ceil(len(update_tasks) / 40))

    async def update_leaderboard_daystart(self):
        update_tasks = []
        async for leaderboard in self.bot.leaderboard_db.find({"autoupdate.leaderboard_daystart": {"$exists": True}}):
            location_id = leaderboard["location_id"]
            location_name = leaderboard["name"]

            players: list[dict] = []
            for player in leaderboard['day-start']:
                players.append(player)
            players.sort(key=lambda x: x['rank'])

            embed = PlayerSimpleEmbed(
                f"Autoupdate Leaderboard daystart {location_name}",
                players[:50], 1)
            embed.description += f'Last updated: <t:{str(datetime.now().timestamp()).split(".")[0]}:R>'

            for autoupdate in leaderboard["autoupdate"]["leaderboard_daystart"]:
                async def update_leaderboard_message(autoupdate: dict, embed: discord.Embed):
                    channel_id = autoupdate["channel_id"]
                    message_id = autoupdate["message_id"]
                    try:
                        await self.bot.http.edit_message(
                            str(channel_id), str(message_id), content="", embeds=[embed.to_dict()])
                    except (discord.NotFound, discord.errors.Forbidden, RuntimeError):
                        await self.bot.leaderboard_db.update_one(
                            {"location_id": location_id},
                            {"$pull": {
                                "autoupdate.leaderboard_daystart": {
                                    "channel_id": channel_id,
                                    "message_id": message_id
                                }
                            }})

                update_tasks.append(
                    update_leaderboard_message(autoupdate, embed))

        logger.debug(f"Autoupdate {len(update_tasks)} daystart leaderboards")

        await run_tasks(update_tasks, math.ceil(len(update_tasks) / 40))

    async def update_player(self, event):
        player_tag = event["tag"]
        player = await self.bot.player_db.find_one({"tag": player_tag, "autoupdate": {"$exists": True}})
        if player is None:
            return

        embed = PlayerOverviewEmbed(player)

        update_tasks = []
        for autoupdate in player["autoupdate"]:
            async def update_player_message(autoupdate: dict, embed: discord.Embed):
                channel_id = autoupdate["channel_id"]
                message_id = autoupdate["message_id"]
                try:
                    await self.bot.http.edit_message(
                        str(channel_id), str(message_id), content="", embeds=[embed.to_dict()])
                except (discord.NotFound, discord.errors.Forbidden, RuntimeError):
                    await self.bot.player_db.update_one(
                        {"tag": player_tag},
                        {"$pull": {
                            "autoupdate": {
                                "channel_id": channel_id,
                                "message_id": message_id
                            }
                        }})

            update_tasks.append(
                update_player_message(autoupdate, embed))

        await run_tasks(update_tasks, math.ceil(len(update_tasks) / 40))


def setup(bot):
    bot.add_cog(AutoUpdate(bot))
