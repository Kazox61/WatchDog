import discord

from watchdog.components import PaginatorResponse


class PlayerSimpleEmbed(discord.Embed):
    def __init__(self, title: str, players: list[dict], start_index: int):
        rows = []
        for i, player in enumerate(players, start_index):
            rows.append(
                f"{str(player['rank']).rjust(3)}{str(player['trophies']).rjust(5)} {player['name']}")
        description = "```" + "###" + "=".rjust(5) + " Name\n"
        description += "\n".join(rows) + "```"
        super().__init__(title=title, description=description)


class PlayerSimplePaginator(PaginatorResponse):
    def __init__(self, title: str, players: list[dict]):
        elements_per_page = 40
        embeds = []
        players_split = [players[i:i + elements_per_page]
                         for i in range(0, len(players), elements_per_page)]
        for i, player_split in enumerate(players_split):
            embeds.append(PlayerSimpleEmbed(
                title, player_split, i*elements_per_page+1))
        super().__init__(embeds)
