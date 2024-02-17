import discord
from discord.ext import commands
import pendulum

from watchdog.custom_bot import CustomBot
from watchdog.components import CommandsMessage


class General(commands.Cog):
    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.slash_command(name="commands")
    async def check_commands(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        help_message = CommandsMessage(self.bot.get_discord_commands())
        await help_message.send(ctx)

    @commands.slash_command(name="info")
    async def general_info(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        description = "My developer is a big fan of Legend League. When he used other tracking bots, "\
                      "they always missed important features, what he needed. So he started to develop me just for himself. "\
                      "Others started to notice the nice features and wanted to use them as well. "\
                      "So my developer made me public for everyone.\n\n"\
                      "To view my commands, use `/commands`. "\
                      "If you like me, feel free to [invite me]("\
                      "https://discord.com/api/oauth2/authorize?client_id=846142858368516158&permissions=8&scope=bot). "\
                      "If you need help, have found a bug or want to request a feature, join my [support server](https://discord.gg/bpQj8aEMxP). "\
                      "If you want to check out my source code, do so on [github.com]("\
                      "https://github.com/Kazox61/WatchDog). "
        embed = discord.Embed(title="Information", description=description)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="Uptime", value=(pendulum.now(
            pendulum.UTC) - self.bot.start_time).in_words(locale='en'))
        embed.add_field(name="Servers", value=len(self.bot.guilds))
        embed.add_field(name="Players", value=await self.bot.player_db.count_documents({}))
        embed.add_field(name="Users", value=await self.bot.user_db.count_documents({}))
        embed.add_field(name="Groups", value=await self.bot.group_db.count_documents({}))
        embed.add_field(name="Leaderboards", value=await self.bot.leaderboard_db.count_documents({}))

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="invite me",
                      url="https://discord.com/api/oauth2/authorize?client_id=846142858368516158&permissions=8&scope=bot", style=discord.ButtonStyle.url))
        view.add_item(discord.ui.Button(label="support server",
                      url="https://discord.gg/bpQj8aEMxP", style=discord.ButtonStyle.url))
        view.add_item(discord.ui.Button(label="code",
                      url="https://github.com/Kazox61/WatchDog", style=discord.ButtonStyle.url))
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    bot.add_cog(General(bot))
