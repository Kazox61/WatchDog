import discord

from watchdog.custom_bot import CustomBot
from watchdog.components.player.embeds import PlayerSeasonOverviewEmbed


class SeasonOverviewOption(discord.SelectOption):
    def __init__(self) -> None:
        super().__init__(label="Season Overview",
                         value="1")

    async def callback(self, interaction: discord.Interaction, player: dict) -> None:
        embed = PlayerSeasonOverviewEmbed(player)
        await interaction.response.send_message(embed=embed)
