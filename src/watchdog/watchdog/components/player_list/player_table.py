import discord

from shared.coc_utils import get_current_insertion_date, SUPER_SCRIPTS
from watchdog.components import PaginatorResponse, PaginatorInteraction


def create_embeds(title: str, players: list[dict]):
    date = get_current_insertion_date()
    elements_per_page = 40
    embeds = []
    rows = []
    for i, player in enumerate(players, 1):
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

        if i % elements_per_page == 0 or i == len(players):
            description = "```" + "###" + "=".rjust(5)
            description += "+".rjust(4) + "-".rjust(6)
            description += "  Name" + "\n" + "\n".join(rows) + "```"
            embed = discord.Embed(title=title, description=description)
            embeds.append(embed)
            rows = []
    return embeds


class PlayerTablePaginatorResponse(PaginatorResponse):
    def __init__(self, title, players: list[dict]):
        embeds = create_embeds(title, players)
        super().__init__(embeds)


class PlayerTablePaginatorInteraction(PaginatorInteraction):
    def __init__(self, title, players: list[dict]):
        embeds = create_embeds(title, players)
        super().__init__(embeds)
