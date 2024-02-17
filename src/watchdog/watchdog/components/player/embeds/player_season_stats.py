import discord


class PlayerSeasonStatsEmbed(discord.Embed):
    def __init__(self, player: dict):
        attacks = []
        defenses = []
        attacks_a_day = []
        defenses_a_day = []
        attack_1stars = []
        attack_2stars = []
        attack_3stars = []
        defense_0stars = []
        defense_1stars = []
        defense_2stars = []
        defense_3stars = []
        for _, battle_log in player["battle_log"].items():
            try:
                attacks.extend(battle_log["attacks"])
            except KeyError:
                pass
            try:
                defenses.extend(battle_log["defenses"])
            except KeyError:
                pass
            try:
                attacks_a_day.append(sum(battle_log["attacks"]))
            except KeyError:
                attacks_a_day.append(0)
            try:
                defenses_a_day.append(sum(battle_log["defenses"]))
            except KeyError:
                defenses_a_day.append(0)
        for trophies_delta in attacks:
            if trophies_delta == 40:
                attack_3stars.append(trophies_delta)
            elif 16 <= trophies_delta <= 32:
                attack_2stars.append(trophies_delta)
            elif 5 <= trophies_delta <= 15:
                attack_1stars.append(trophies_delta)
        for trophies_delta in defenses:
            if abs(trophies_delta) == 40:
                defense_3stars.append(trophies_delta)
            elif 16 <= abs(trophies_delta) <= 32:
                defense_2stars.append(trophies_delta)
            elif 5 <= abs(trophies_delta) <= 15:
                defense_1stars.append(trophies_delta)
            elif trophies_delta == 0:
                defense_0stars.append(0)
        try:
            hitrate = round(len(attack_3stars) / (len(attack_3stars) +
                            len(attack_2stars) + len(attack_1stars)) * 100, 2)
        except ZeroDivisionError:
            hitrate = 0
        header = f"{player['name']} | {player['tag']}\n"
        body = ''
        try:
            body += f"- avg Trophies per attack: {round(sum(attacks) / len(attacks))}\n"
        except ZeroDivisionError:
            pass
        try:
            body += f"- avg Trophies per defense: {round(sum(defenses) / len(defenses))}\n"
        except ZeroDivisionError:
            pass
        try:
            body += f"- avg Trophies per day in offense: {round(sum(attacks_a_day) / len(attacks_a_day))}\n"
        except ZeroDivisionError:
            pass
        try:
            body += f"- avg Trophies per day in defense: {round(sum(defenses) / len(defenses_a_day))}\n"
        except ZeroDivisionError:
            pass
        body += f"- 3 Star Hitrate {hitrate}%\n"
        body += f"- total 3 stars in offense: {len(attack_3stars)}\n"
        body += f"- total 2 stars in offense: {len(attack_2stars)}\n"
        body += f"- total 1 stars in offense: {len(attack_1stars)}\n"
        body += f"- total 3 stars in defense: {len(defense_3stars)}\n"
        body += f"- total 2 stars in defense: {len(defense_2stars)}\n"
        body += f"- total 1 stars in defense: {len(defense_1stars)}\n"
        body += f"- total 0 stars in defense: {len(defense_0stars)}\n"
        super().__init__(title=header, description=body)
