import discord
from discord.ext import commands

from watchdog.custom_bot import CustomBot


class DiscordEvents(commands.Cog):
    def __init__(self, bot: CustomBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_connect(self):
        channel = await self.bot.fetch_channel(self.bot.config.introduction_channel_id)
        await channel.purge(limit=100)

        discord_commands = self.bot.get_discord_commands()
        await channel.send("**Introducing our Discord Bot for Clash of Clans Legend League tracking!**\n\n**How It Works:**\nOur bot uses the Clash of Clans API to fetch the trophies of each player added to our bot. The Clash of Clans API updates their data each minute. This means our bot will compare each minute the trophies and detect the trophy difference. So if multiple attacks/defenses happen simultaneously the bot can't track them.\n\n**Commands:**\n")
        for category, commands in discord_commands.items():
            text = f"- **{category.lower()}**\n"
            for command in commands:
                text += f"  - `{command['name']}"
                for param in command["params"]:
                    text += f" <{param}>"
                text += "`\n"
                description = command["description"]
                if description != "No description provided":
                    text += "    " + description + "\n"

            await channel.send(text)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        msg = "Thanks for inviting LegendWatchDog to your server. This bot is all about the Legend League. " \
              "I suggest you to look into the `help` command to see and learn more about all existing commands."

        channel = self.bot.get_channel(self.bot.config.server_join_channel_id)
        await channel.send(f"Just joined `{guild.name}`, {guild.member_count} members")

        for guildChannel in guild.channels:
            permissions = guildChannel.permissions_for(guildChannel.guild.me)
            if str(guildChannel.type) == 'text' and permissions.send_messages is True:
                firstChannel = guildChannel
                break
        else:
            return

        embed = discord.Embed(description=msg, color=discord.Color.blue())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Support Server",
            emoji="🔗",
            url="https://discord.gg/TZeXsbbQ9y",
            style=discord.ButtonStyle.url))
        embed.set_footer(
            text="Admin permissions are recommended for full functionality.")
        await firstChannel.send(view=view, embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        channel = self.bot.get_channel(self.bot.config.server_join_channel_id)
        await channel.send(f"Just left `{guild.name}`, {guild.member_count} members")


def setup(bot):
    bot.add_cog(DiscordEvents(bot))
