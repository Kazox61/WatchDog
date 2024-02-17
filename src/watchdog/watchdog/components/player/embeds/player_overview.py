import discord
from itertools import zip_longest

from shared.coc_utils import get_current_insertion_date, SUPER_SCRIPTS


class PlayerOverviewEmbed(discord.Embed):
    def __init__(self, player: dict):
        if player is None:
            header = "Currently not available!"
            super().__init__(title=header)
            return

        player_tag = player["tag"]
        key = get_current_insertion_date()

        if key not in player["battle_log"]:
            header = f"{player['name']} | {player_tag}"
            body = "Currently not available!"
            super().__init__(title=header, description=body)
            return

        stats_today = player["battle_log"][key]
        try:
            reset_trophies = stats_today["reset_trophies"]
        except KeyError:
            reset_trophies = 0
        try:
            attacks = stats_today["attacks"]
        except KeyError:
            attacks = []
        sum_attacks = sum(attacks)
        try:
            defenses = stats_today["defenses"]
        except KeyError:
            defenses = []
        sum_defenses = sum(defenses)
        trophies_delta = sum_attacks + sum_defenses
        end_trophies = reset_trophies + trophies_delta
        body = f"**Overview**\n"
        body += f"- Start Trophies: {str(reset_trophies)}\n"
        body += f"- End Trophies: {str(end_trophies)}\n"
        body += f"- Delta Trophies: {str(trophies_delta)}\n"
        body += f'```{"Attacks".ljust(10)}{"Defenses".ljust(10)}\n'
        body += f'{str(sum_attacks).rjust(4) + SUPER_SCRIPTS[len(attacks)]}     {str(sum_defenses).rjust(4) + SUPER_SCRIPTS[len(defenses)]}\n'
        for a, d in zip_longest(attacks, defenses, fillvalue=""):
            if a == "" and d == "":
                break
            body += f'{str(a).rjust(4)}      {str(d).rjust(4)}\n'
        body += "```"

        header = f"{player['name']} | {player_tag}"
        super().__init__(title=header, description=body)
