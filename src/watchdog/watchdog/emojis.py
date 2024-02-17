import discord


class EmojiType:
    def __init__(self, emoji_string: str) -> None:
        self.emoji_string = emoji_string

    def __str__(self) -> str:
        return self.emoji_string

    @property
    def partial_emoji(self):
        emoji = self.emoji_string.split(":")
        animated = "<a:" in self.emoji_string
        emoji = discord.PartialEmoji(name=emoji[1][1:], id=int(
            str(emoji[2])[:-1]), animated=animated)
        return emoji


class Emojis():
    attack = EmojiType("<:attack:1122637998312407122>")
    defense = EmojiType("<:defense:1122638046962139256>")
    plus = EmojiType("<:plus:1124278557665931316>")
    minus = EmojiType("<:minus:1124278554675392544>")
    stats = EmojiType("<:stats:1124125707392520193>")
    observe = EmojiType("<:observe:1124127995020451940>")
    addtolog = EmojiType("<:addtolog:1124131916405280848>")
    removefromlog = EmojiType("<:removefromlog:1124242230773817444>")
    settings = EmojiType("<:settings:1124242288428711976>")
    home = EmojiType("<:home:1124677834661691403>")
    number_0 = EmojiType("<:0_:1122657206047879198>")
    number_1 = EmojiType("<:1_:1122657223471022120>")
    number_2 = EmojiType("<:2_:1122657220384014367>")
    number_3 = EmojiType("<:3_:1122657218769190932>")
    number_4 = EmojiType("<:4_:1122657217196327002>")
    number_5 = EmojiType("<:5_:1122657214717509794>")
    number_6 = EmojiType("<:6_:1122657212712615968>")
    number_7 = EmojiType("<:7_:1122657210351231127>")
    number_8 = EmojiType("<:8_:1122657208493150348>")
    number_9 = EmojiType("<:9_:1122657226012766208>")
