import discord

from watchdog.components import PaginatorResponse


class PlayerSimplePaginator(PaginatorResponse):
    def __init__(self, title: str, players: list[dict]):
        if not players:
            return None
        elements_per_page = 40
        embeds = []
        rows = []
        for i, player in enumerate(players, 1):
            rows.append(
                f"{str(player['rank']).rjust(3)}{str(player['trophies']).rjust(5)} {player['name']}")

            if i % elements_per_page == 0 or i == len(players):
                description = "```" + "###" + "=".rjust(5) + " Name\n"
                description += "\n".join(rows) + "```"
                embed = discord.Embed(title=title, description=description)
                embeds.append(embed)
                rows = []
        super().__init__(embeds)
