import discord
from discord.ext import commands
import coc
import asyncio
from bson import ObjectId

from watchdog.custom_bot import CustomBot
from watchdog.cogs.group import Group
from watchdog.cogs.player import Player
from watchdog.cogs.leaderboard import Leaderboard
from watchdog.components import Question, Dropdown, ClanSetup


class Setup(commands.Cog):
    setup = discord.SlashCommandGroup(name="setup")

    def __init__(self, bot: CustomBot):
        self.bot = bot
        self.group_cog: Group = self.bot.get_cog("Group")
        self.player_cog: Player = self.bot.get_cog("Player")
        self.leaderboard_cog: Leaderboard = self.bot.get_cog("Leaderboard")

    @setup.command(name="clan", description="A fast way to setup a group and autoupdates for your Clan")
    @discord.commands.option(name="clantag", description="Choose the clan you want to setup")
    @discord.commands.option(name="role", description="Choose a role from where you want to copy the members to your Group.")
    async def setup_clan(self,
                         ctx: discord.ApplicationContext,
                         clantag: str,
                         role: discord.Role):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        try:
            clan = await self.bot.coc_client.get_clan(clantag)
        except coc.NotFound:
            await ctx.respond("Clantag not found.")
            return

        legend_clan_members = [
            clan_member for clan_member in clan.members if clan_member.league and clan_member.league.name == "Legend League"]
        legend_clan_members.sort(
            key=lambda member: member.trophies, reverse=True)

        clan_setup = ClanSetup(clan, legend_clan_members)
        canceled, [create_group, autoupdate_group, split_channels_autoupdate_players, autoupdate_global_leaderboard, autoupdate_local_leaderboard] = await clan_setup.send(ctx)

        if canceled:
            return

        if create_group:
            i = 0
            while True:
                group_id = await self.group_cog.try_create_group(
                    clan.name + " " + str(i) if i > 0 else clan.name, "Public", ctx.user.id)
                if group_id is not None:
                    break
                i += 1

            tasks = []
            for legend_clan_member in legend_clan_members:
                task = asyncio.ensure_future(self.group_cog.try_add_player_to_group(
                    group_id, legend_clan_member.tag))
                tasks.append(task)
            await asyncio.gather(*tasks)

            for member in role.members:
                await self.bot.try_create_user(member.id)
                await self.bot.group_db.update_one(
                    {"_id": ObjectId(group_id)}, {"$addToSet": {'members': member.id}})

        if not any([create_group, autoupdate_group, split_channels_autoupdate_players, autoupdate_global_leaderboard, autoupdate_local_leaderboard]):
            return

        category_channel = await ctx.guild.create_category_channel("WatchDog")

        if autoupdate_group:
            group_channel = await category_channel.create_text_channel("Group")
            await self.group_cog.try_add_autoupdate(group_id, group_channel)

        async def create_player_autoupdate(player: coc.ClanMember, channel: discord.TextChannel = None):
            if channel is None:
                channel = await category_channel.create_text_channel(player.name)
            await self.player_cog.try_add_autoupdate(player.tag, channel, ctx.user.id)

        if not split_channels_autoupdate_players:
            player_channel = await category_channel.create_text_channel("Players")

        tasks = []
        for player in legend_clan_members:
            if split_channels_autoupdate_players:
                task = asyncio.ensure_future(
                    create_player_autoupdate(player))
            else:
                task = asyncio.ensure_future(
                    create_player_autoupdate(player, player_channel))
        await asyncio.gather(*tasks)

        if autoupdate_global_leaderboard:
            global_channel = await category_channel.create_text_channel("Leaderboard global")
            await self.leaderboard_cog.autoudate_leaderboard_daystart("global", "global", global_channel, ctx.user.id)
            await self.leaderboard_cog.autoupdate_leaderboard_current("global", global_channel, ctx.user.id)

        if autoupdate_local_leaderboard:
            location_name = clan.location.name
            location_id = str(clan.location.id)
            local_channel = await category_channel.create_text_channel(f"Leaderboard {location_name}")
            await self.leaderboard_cog.autoudate_leaderboard_daystart(location_name, location_id, local_channel, ctx.user.id)
            await self.leaderboard_cog.autoupdate_leaderboard_current(location_id, local_channel, ctx.user.id)


def setup(bot):
    bot.add_cog(Setup(bot))
