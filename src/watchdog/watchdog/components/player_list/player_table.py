import discord

from shared.coc_utils import get_current_insertion_date, SUPER_SCRIPTS
from watchdog.components import PaginatorResponse, PaginatorInteraction


class PlayerTableEmbed(discord.Embed):
    def __init__(self, title: str, players: list[dict], start_index: int):
        date = get_current_insertion_date()
        rows = []
        for i, player in enumerate(players, start_index):
            if "battle_log" in player and date in player['battle_log']:
                battle_log = player['battle_log'][date]

                sum_attacks = sum(battle_log['attacks'])
                sum_defenses = sum(battle_log['defenses'])
                attack = str(sum_attacks) + \
                    SUPER_SCRIPTS[len(battle_log['attacks'])]
                defense = str(sum_defenses) + \
                    SUPER_SCRIPTS[len(battle_log['defenses'])]

                rows.append(
                    f"{str(i).rjust(3)}{str(player['trophies']).rjust(5)}{attack.rjust(5)}{defense.rjust(6)} {player['name']}")
            else:
                rows.append(
                    f"{str(i).rjust(3)}{str(player['trophies']).rjust(5)}{' ' * 11} {player['name']}")

            description = "```" + "###" + "=".rjust(5)
            description += "+".rjust(4) + "-".rjust(6)
            description += "  Name" + "\n" + "\n".join(rows) + "```"
        super().__init__(title=title, description=description)


def create_embeds(title: str, players: list[dict]):
    elements_per_page = 40
    embeds = []
    players = []
    players_split = [players[i:i + elements_per_page]
                     for i in range(0, len(players), elements_per_page)]
    for i, player_split in enumerate(players_split):
        embeds.append(PlayerTableEmbed(
            title, player_split, i*elements_per_page+1))
    return embeds


class PlayerTablePaginatorResponse(PaginatorResponse):
    def __init__(self, title, players: list[dict]):
        embeds = create_embeds(title, players)
        super().__init__(embeds)


class PlayerTablePaginatorInteraction(PaginatorInteraction):
    def __init__(self, title, players: list[dict]):
        embeds = create_embeds(title, players)
        super().__init__(embeds)
