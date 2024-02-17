import discord

from . import PaginatorResponse


class CommandsMessage(PaginatorResponse):
    def __init__(self, discord_commands: dict, user_id: int = None):
        embeds = []
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
