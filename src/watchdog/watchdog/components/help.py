import discord

from . import PaginatorResponse


class HelpMessage(PaginatorResponse):
    def __init__(self, discord_commands: dict, user_id: int = None):
        embeds = [discord.Embed(title="Help", description="**Introducing our Discord Bot for Clash of Clans Legend League tracking!**\n\n**How It Works:**\nOur bot uses the Clash of Clans API to fetch the trophies of each player added to our bot. The Clash of Clans API updates their data each minute. This means our bot will compare each minute the trophies and detect the trophy difference. So if multiple attacks/defenses happen simultaneously the bot can't track them.")]
        for category, commands in discord_commands.items():
            text = ""
            for command in commands:
                text += f"- `{command['name']}"
                for param in command["params"]:
                    text += f" <{param}>"
                text += "`\n"
                description = command["description"]
                if description != "No description provided":
                    text += "  " + description + "\n"
            embeds.append(discord.Embed(
                title=category.lower() + " commands", description=text))
        super().__init__(embeds, user_id)
