import discord
from discord.ext import commands
import pendulum

from watchdog.custom_bot import CustomBot
from watchdog.components import HelpMessage


class General(commands.Cog):
    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.slash_command(name="help")
    async def help(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        help_message = HelpMessage(self.bot.get_discord_commands())
        await help_message.send(ctx)

    @commands.slash_command(name="info")
    async def general_info(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        description = f"Uptime: {(pendulum.now(pendulum.UTC) - self.bot.start_time).in_words(locale='en')}\n"\
                      f"Servers: {len(self.bot.guilds)}\n"\
                      f"Players: {await self.bot.player_db.count_documents({})}\n"\
                      f"Users: {await self.bot.user_db.count_documents({})}\n"\
                      f"Groups: {await self.bot.group_db.count_documents({})}\n"

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite me", emoji="🔗",
                      url="https://discord.com/api/oauth2/authorize?client_id=846142858368516158&permissions=8&scope=bot", style=discord.ButtonStyle.url))
        view.add_item(discord.ui.Button(label="Support Server", emoji="🔗",
                      url="https://discord.gg/bpQj8aEMxP", style=discord.ButtonStyle.url))
        embed = discord.Embed(title="Information", description=description)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(General(bot))
