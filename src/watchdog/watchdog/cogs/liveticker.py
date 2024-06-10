import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import traceback


from watchdog.custom_bot import CustomBot
from watchdog.background import player_event_emitter
from watchdog import logger
from watchdog.components import PlayerOverviewEmbed


class Liveticker(commands.Cog):
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot
        self.player_event_emitter = player_event_emitter
        self.player_event_emitter.on(
            "diffTrophies", self.on_player_trophies_changed)
        self.updated_players = {}
        # self.update_loop.start()

    async def on_player_trophies_changed(self, event):
        self.updated_players[event["tag"]] = event["diffTrophies"]

    async def get_liveticker_data(self, updated_players) -> tuple[dict[int, list], dict[str, tuple]]:
        player_channels: dict[int, list] = {}
        player_data: dict[str, tuple] = {}
        for player_tag, trophies_delta in updated_players.items():
            channels = await self.bot.group_db.distinct("channel_id", {"players": player_tag})
            player = await self.bot.get_player(player_tag)
            player_data[player_tag] = player, trophies_delta
            for channel in channels:
                if channel in player_channels:
                    player_channels[channel].append(player_tag)
                else:
                    player_channels[channel] = [player_tag]
        return player_channels, player_data

    async def wait_for_reaction(self, msg: discord.Message, player_embeds: list[discord.Embed], overview_embed: discord.Embed):
        home_emoji = self.bot.emoji.home

        def check(reaction: discord.Reaction, user: discord.User):
            return (str(reaction.emoji) in [str(x) for x in self.bot.number_emojis] or str(reaction.emoji) == str(home_emoji)) and not user.bot and msg.id == reaction.message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=3600, check=check)
                if str(reaction.emoji) == str(home_emoji):
                    await msg.edit(embed=overview_embed)
                else:
                    index = 0
                    for i, emoji in enumerate(self.bot.number_emojis):
                        if str(emoji) == str(reaction.emoji):
                            index = i-1
                            break
                    await msg.edit(embed=player_embeds[index])
                await msg.remove_reaction(reaction.emoji, user)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                    return
                except:
                    return
            except discord.errors.Forbidden:
                return

    async def send_updated_player(self, channel_id, player_tags, player_data):
        try:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                return
            text = ""
            player_embeds = []
            remaining_players = player_tags.copy()
            position = 0
            for player_tag in player_tags:
                try:
                    if position > 7:
                        await self.send_updated_player(channel_id, remaining_players, player_data)
                        break
                    player, trophies_delta = player_data[player_tag]
                    text += self.create_string(player,
                                               trophies_delta, position + 1) + "\n"
                    player_embed = PlayerOverviewEmbed(player)
                    player_embeds.append(player_embed)
                    remaining_players.pop(0)
                    position += 1
                except discord.DiscordException:
                    # TODO: DM Owner one time to fix permissions
                    logger.warn(f"Missing Permissions in {channel.name}")
                except Exception as e:
                    logger.error(str(e))
                    traceback_str = traceback.format_exc()
                    logger.error(traceback_str)
            text += f'<t:{str(datetime.now().timestamp()).split(".")[0]}:R>'
            if len(player_embeds) < 1:
                return
            overview_embed = discord.Embed(description=text)
            msg = await channel.send(embed=overview_embed)
            await msg.add_reaction(self.bot.emoji.home.partial_emoji)
            for i in range(len(player_embeds)):
                await msg.add_reaction(self.bot.get_number_emoji(i + 1).partial_emoji)
            asyncio.ensure_future(self.wait_for_reaction(
                msg, player_embeds, overview_embed))
        except discord.NotFound:
            # TODO: DM Owner once to set a new valid channel
            logger.error(
                f"Channel can't be found. Implement DMing Owner to notify him")

    def create_string(self, player, trophies_delta, position) -> str:
        if trophies_delta > 0:
            text = f"{self.bot.get_number_emoji(position).partial_emoji} {self.bot.emoji.attack.partial_emoji} `{str(trophies_delta).rjust(4)} | "
        else:
            text = f"{self.bot.get_number_emoji(position).partial_emoji} {self.bot.emoji.defense.partial_emoji} `{str(trophies_delta).rjust(4)} | "
        text += player["name"] + "`"
        return text

    @tasks.loop(minutes=1)
    async def update_loop(self):
        updated_players = self.updated_players.copy()
        self.updated_players.clear()
        player_channels, player_data = await self.get_liveticker_data(updated_players)
        update_tasks = []
        for channel_id, player_tags in player_channels.items():
            update_tasks.append(self.send_updated_player(
                channel_id,
                player_tags,
                player_data))
        asyncio.gather(*update_tasks)


def setup(bot):
    bot.add_cog(Liveticker(bot))
