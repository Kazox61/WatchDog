import discord
from discord.interactions import Interaction

from watchdog.custom_bot import CustomBot
from watchdog.components.player.player_search import SeasonDaysOption, SeasonOverviewOption, SeasonStatsOption


class PlayerSearchDropdown(discord.ui.Select):
    def __init__(self, bot: CustomBot, player_tag: str):
        self.bot = bot
        self.player_tag = player_tag
        self.player_search_options = [
            SeasonDaysOption(),
            SeasonOverviewOption(),
            SeasonStatsOption()
        ]

        super().__init__(
            placeholder="Options",
            min_values=1,
            max_values=1,
            options=self.player_search_options
        )

    async def callback(self, interaction: Interaction):
        player = await self.bot.get_player(self.player_tag)

        for option in self.player_search_options:
            if self.values[0] != option.value:
                continue

            await option.callback(interaction, player)


class PlayerSearchView(discord.ui.View):
    def __init__(self, bot: CustomBot, player_tag: str):
        super().__init__()
        self.add_item(PlayerSearchDropdown(bot, player_tag))
