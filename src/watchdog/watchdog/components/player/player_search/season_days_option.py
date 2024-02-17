from itertools import zip_longest
import discord

from shared.coc_utils import get_season_days, SUPER_SCRIPTS
from watchdog.custom_bot import CustomBot
from watchdog.components import PaginatorInteraction


class SeasonDaysOption(discord.SelectOption):
    def __init__(self) -> None:
        super().__init__(label="Season Days",
                         value="0")

    async def callback(self, interaction: discord.Interaction, player: dict) -> None:
        paginator = SeasonDaysPaginator(player)
        await paginator.send(interaction)


class SeasonDaysPaginator(PaginatorInteraction):
    def __init__(self, player: dict, user_id: int = None):
        keys = get_season_days()
        embeds = []
        battle_log: dict = player["battle_log"]
        days = len(keys)
        len_days = len(str(days))
        for i, key in enumerate(keys):
            if key not in battle_log:
                continue

            date = key[6:8] + "." + key[4:6]
            header = f'**{player["name"]} | {player["tag"]}**\nDay {str(i+1).rjust(len_days)} {date}'

            stats = battle_log.get(key)
            embeds.append(PlayerDayEmbed(header, stats))

        embeds.reverse()
        super().__init__(embeds, user_id)


class PlayerDayEmbed(discord.Embed):
    def __init__(self, header, stats):
        try:
            reset_trophies = stats["reset_trophies"]
        except KeyError:
            reset_trophies = 0
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
        super().__init__(title=header, description=body)
