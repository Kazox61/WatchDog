import discord

from watchdog.custom_bot import CustomBot
from watchdog.components.player.embeds import PlayerSeasonStatsEmbed


class SeasonStatsOption(discord.SelectOption):
    def __init__(self) -> None:
        super().__init__(label="Season Stats",
                         value="2")

    async def callback(self, interaction: discord.Interaction, player: dict) -> None:
        embed = PlayerSeasonStatsEmbed(player)
        await interaction.response.send_message(embed=embed)
