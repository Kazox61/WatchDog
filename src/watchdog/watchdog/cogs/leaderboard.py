import discord
from discord.ext import commands

from watchdog.custom_bot import CustomBot
from watchdog.components import PlayerSimplePaginator, PlayerOverviewEmbed, PlayerTablePaginatorResponse, PaginatorResponse
from watchdog.autocomplete import search_location, locations


class Leaderboard(commands.Cog):
    leaderboard = discord.SlashCommandGroup(
        "leaderboard", "All Leaderboard commands")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @leaderboard.command(name="day-start", description="Get the ranking from a day-start leaderboard.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_day_start(self,
                                    ctx: discord.ApplicationContext,
                                    location: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        result = await self.bot.leaderboard_db.find_one({'location': location})
        if result is None:
            await ctx.respond("Location is not tracked yet, use `leaderboard add`.")
            return
        players: list[dict] = []
        for player in result['leaderboard']:
            players.append(player)
        players.sort(key=lambda x: x['rank'])

        paginator = PlayerSimplePaginator(
            f'Leaderboard day-start {location}', players)
        await paginator.send(ctx)

    @leaderboard.command(name="current", description="Get a overview of the players from a current leaderboard ranking.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_current(self,
                                  ctx: discord.ApplicationContext,
                                  location: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Country not found.")
            return

        country_id = locations[location]
        country_name = location

        if country_id == 'global':
            rank_players = await self.bot.coc_client.get_location_players()
        else:
            rank_players = await self.bot.coc_client.get_location_players(country_id)

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
            f"Leaderboard current `{country_name}`",
            players)
        await paginator.send(ctx)

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

    @leaderboard.command(name="add", description="Choose a location which you'd like to see the day-start leaderboard. Available on the next day.")
    @discord.commands.option("location", description="Choose a location", autocomplete=search_location)
    async def leaderboard_add(self,
                              ctx: discord.ApplicationContext,
                              location: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        if location not in locations.keys():
            await ctx.respond("Location doesn't exist.")
            return

        count = await self.bot.leaderboard_db.count_documents(
            {'location': location})
        if count > 0:
            await ctx.respond("Location already exist in database.")
            return

        await self.bot.leaderboard_db.insert_one(
            {'location': location, 'leaderboard': []})
        await ctx.respond(f"Location `{location}` added successfully.")


def setup(bot):
    bot.add_cog(Leaderboard(bot))
