import discord
from discord.ext import commands
import coc

from watchdog.custom_bot import CustomBot
from watchdog.autocomplete import search_player, parse_player
from watchdog.components import PlayerOverviewEmbed, PlayerSearchView


class Player(commands.Cog):
    player = discord.SlashCommandGroup("player", "All Player commands")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @player.command(name="search", description="Search a player by name or tag, if the player is not suggested, you can add him by his tag.")
    @discord.commands.option("player", description="Choose a player or add a missing one with a tag", autocomplete=search_player)
    async def player_search(self,
                            ctx: discord.ApplicationContext,
                            player: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        player_tag = parse_player(player)

        valid = coc.utils.is_valid_tag(player_tag)
        if not valid:
            await ctx.respond("Player tag is invalid")
            return

        try:
            # check if player exists
            await self.bot.coc_client.get_player(player_tag)
        except coc.NotFound:
            await ctx.respond(f'A player with {player_tag} doesnt exist.')
            return

        await self.bot.try_create_player(player_tag)

        player = await self.bot.get_player(player_tag)

        embed = PlayerOverviewEmbed(player)

        view = PlayerSearchView(self.bot, player_tag)

        await ctx.respond(view=view, embed=embed)

    @player.command(name="autoupdate", description="Add Autoupdate for a Player.")
    @discord.commands.option("player", description="Choose a player or add a missing one with a tag", autocomplete=search_player)
    async def player_autoupdate(self,
                                ctx: discord.ApplicationContext,
                                player: str,
                                channel: discord.TextChannel):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        player_tag = parse_player(player)

        valid = coc.utils.is_valid_tag(player_tag)
        if not valid:
            await ctx.respond("Player tag is invalid")
            return

        try:
            # check if player exists
            player = await self.bot.coc_client.get_player(player_tag)
        except coc.NotFound:
            await ctx.respond(f'A player with {player_tag} doesnt exist.')
            return

        success = self.bot.user_has_write_permission(ctx.user, channel) and await self.try_add_autoupdate(player_tag, channel, ctx.user.id)

        await ctx.respond(f"Successfully added Autoupdate for `{player.name}` in {channel.mention}."
                          if success else
                          f"Failed to add Autoupdate for `{player.name}` in {channel.mention}.")

    async def try_add_autoupdate(self, player_tag: str, channel: discord.TextChannel, discord_user_id: str) -> bool:
        await self.bot.try_create_player(player_tag)
        player = await self.bot.player_db.find_one({"tag": player_tag})

        try:
            message = await channel.send(embed=PlayerOverviewEmbed(player))
        except:
            return False

        document = {
            "discord_user_id": discord_user_id,
            "channel_id": channel.id,
            "message_id": message.id
        }

        result = await self.bot.player_db.update_one({"tag": player_tag}, {
            "$addToSet": {f"autoupdate": document}})
        return result.modified_count > 0


def setup(bot):
    bot.add_cog(Player(bot))
