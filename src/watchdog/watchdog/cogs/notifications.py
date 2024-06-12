import discord
from discord.ext import commands
import asyncio


from watchdog.custom_bot import CustomBot
from watchdog.background import player_event_emitter


class Notifications(commands.Cog):
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.player_event_emitter = player_event_emitter
        # self.player_event_emitter.on("diffTrophies", self.on_player_trophies_changed)

    async def on_player_trophies_changed(self, event):
        tag = event["tag"]
        diff_trophies = event["diffTrophies"]

        subscribers = await self.bot.group_db.distinct("notifications", {"players": tag})
        tasks = []
        player = await self.bot.player_db.find_one({"tag": tag})
        message = f"`{player['name']}` got `{diff_trophies}`"
        for subscriber in subscribers:
            tasks.append(self.dm_user(subscriber, message))
        await asyncio.gather(*tasks)

    async def dm_user(self, discord_id: int, message: str):
        try:
            user = await self.bot.get_or_fetch_user(discord_id)
            await user.send(content=message)
        except discord.Forbidden:
            pass


def setup(bot):
    bot.add_cog(Notifications(bot))
