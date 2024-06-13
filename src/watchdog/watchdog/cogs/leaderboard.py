import discord
from discord.ext import commands
from datetime import datetime

from watchdog.custom_bot import CustomBot
from watchdog.components import PlayerSimplePaginator, PlayerOverviewEmbed, PlayerTablePaginatorResponse, PaginatorResponse, PlayerSimpleEmbed
from watchdog.autocomplete import search_location, locations


class Leaderboard(commands.Cog):
    leaderboard = discord.SlashCommandGroup(
        "leaderboard", "All Leaderboard commands")
    leaderboard_current = leaderboard.create_subgroup(
        name="current", description="All Leaderboard Current commands")
    leaderboard_daystart = leaderboard.create_subgroup(
        name="daystart", description="All Leaderboard Daystart commands")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @leaderboard_daystart.command(name="check", description="Get the ranking from a daystart leaderboard.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_daystart_check(self,
                                         ctx: discord.ApplicationContext,
                                         location: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        result = await self.bot.leaderboard_db.find_one({'name': location})

        players: list[dict] = []
        for player in result['day-start']:
            players.append(player)
        players.sort(key=lambda x: x['rank'])

        paginator = PlayerSimplePaginator(
            f'Leaderboard daystart {location}', players)
        await paginator.send(ctx)

    @leaderboard_daystart.command(name="autoupdate", description="Add Autoupdate for daystart Leaderboard.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_daystart_autoupdate(self,
                                              ctx: discord.ApplicationContext,
                                              location: str,
                                              channel: discord.TextChannel):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        location_id = locations[location]
        location_name = location

        success = self.bot.user_has_write_permission(ctx.user, channel) and await self.autoudate_leaderboard_daystart(location_name, location_id, channel, ctx.user.id)

        await ctx.respond(f"Successfully added Autoupdate for `{location_name}` in {channel.mention}."
                          if success else
                          f"Failed to add Autoupdate for `{location_name}` in {channel.mention}.")

    @leaderboard_current.command(name="check", description="Get a overview of the players from a current leaderboard ranking.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_current_check(self,
                                        ctx: discord.ApplicationContext,
                                        location: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        location_id = locations[location]
        location_name = location

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

        paginator = PlayerTablePaginatorResponse(
            f"Leaderboard current `{location_name}`",
            players)
        await paginator.send(ctx)

    @leaderboard_current.command(name="autoupdate", description="Add Autoupdate for current Leaderboard.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_current_autoupdate(self,
                                             ctx: discord.ApplicationContext,
                                             location: str,
                                             channel: discord.TextChannel):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        location_id = locations[location]
        location_name = location

        success = self.bot.user_has_write_permission(ctx.user, channel) and await self.autoupdate_leaderboard_current(location_id, channel, ctx.user.id)

        await ctx.respond(f"Successfully added Autoupdate for `{location_name}` in {channel.mention}."
                          if success else
                          f"Failed to add Autoupdate for `{location_name}` in {channel.mention}.")

    @leaderboard.command(name="stats", description="Get the individual stats for a current leaderboard ranking.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_stats(self,
                                ctx: discord.ApplicationContext,
                                location: str):
        await ctx.response.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        location_id = locations[location]
        if location_id == 'global':
            players = await self.bot.coc_client.get_location_players()
        else:
            players = await self.bot.coc_client.get_location_players(location_id)
        embeds = []
        for ranked_player in players:
            player = await self.bot.get_player(ranked_player.tag)
            embed = PlayerOverviewEmbed(player)
            embeds.append(embed)

        paginator = PaginatorResponse(embeds)
        await paginator.send(ctx)

    async def autoudate_leaderboard_daystart(self, location_name: str, location_id: str, channel: discord.TextChannel, discord_user_id: int) -> bool:
        try:
            result = await self.bot.leaderboard_db.find_one({'location_id': location_id})

            players: list[dict] = []
            for player in result['day-start']:
                players.append(player)
            players.sort(key=lambda x: x['rank'])

            embed = PlayerSimpleEmbed(
                f"Autoupdate Leaderboard daystart {location_name}",
                players[:50], 1)
            embed.description += f'Last updated: <t:{str(datetime.now().timestamp()).split(".")[0]}:R>'

            message = await channel.send(embed=embed)

        except:
            return False

        document = {
            "discord_user_id": discord_user_id,
            "channel_id": channel.id,
            "message_id": message.id
        }

        result = await self.bot.leaderboard_db.update_one({"location_id": location_id}, {
            "$addToSet": {f"autoupdate.leaderboard_daystart": document}})
        return result.modified_count > 0

    async def autoupdate_leaderboard_current(self, location_id: str, channel: discord.TextChannel, discord_user_id: int) -> bool:
        try:
            message = await channel.send("Loading...")
        except:
            return False

        document = {
            "discord_user_id": discord_user_id,
            "channel_id": channel.id,
            "message_id": message.id
        }

        result = await self.bot.leaderboard_db.update_one({"location_id": location_id}, {
            "$addToSet": {f"autoupdate.leaderboard_current": document}})
        return result.modified_count > 0


def setup(bot):
    bot.add_cog(Leaderboard(bot))
