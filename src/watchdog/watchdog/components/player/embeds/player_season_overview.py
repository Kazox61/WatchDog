import discord

from shared.coc_utils import get_season_days


class PlayerSeasonOverviewEmbed(discord.Embed):
    def __init__(self, player):
        keys = get_season_days()

        body = f"```"
        battle_log: dict = player["battle_log"]
        days = len(keys)
        len_days = len(str(days))
        for i, key in enumerate(keys):
            if key not in battle_log:
                continue
            stats = battle_log.get(key)

            try:
                reset_trophies = stats["reset_trophies"]
                # TODO: prevent this before data in db
                if i == 0 and reset_trophies > 5000:
                    reset_trophies = 5000
            except KeyError:
                reset_trophies = ""

            try:
                attacks = stats["attacks"]
            except KeyError:
                attacks = []
            sum_attacks = sum(attacks)
            try:
                defenses = stats["defenses"]
            except KeyError:
                defenses = []
            sum_defenses = sum(defenses)

            body += f"Day {str(i+1).rjust(len_days)} {str(reset_trophies).rjust(5)} {str(sum_attacks).rjust(4)} {str(sum_defenses).rjust(5)}\n"
        body += "```"

        header = f'**{player["name"]} | {player["tag"]}**\n'

        super().__init__(title=header, description=body)
