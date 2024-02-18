import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime

from watchdog.custom_bot import CustomBot
from watchdog.cogs.group import sort_by_current_trophies
from watchdog.components import PlayerTableEmbed


class AutoUpdate(commands.Cog):
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.update_loop.start()

    @tasks.loop(minutes=1)
    async def update_loop(self):
        await self.update_groups()
        await self.update_leaderboard_current()

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
                    except:
                        pass

                update_tasks.append(update_group_message(autoupdate, embed))

        await asyncio.gather(*update_tasks)

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
                    except:
                        pass

                update_tasks.append(
                    update_leaderboard_message(autoupdate, embed))

        await asyncio.gather(*update_tasks)


def setup(bot):
    bot.add_cog(AutoUpdate(bot))
