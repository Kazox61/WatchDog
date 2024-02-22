import discord


class Question(discord.ui.View):
    def __init__(self, options: list, question: str = None, embed=None):
        items = []
        for option in options:
            button = discord.ui.Button(
                label=option["label"], style=option["style"])
            button.callback = lambda iteraction, value=option["value"]: self.callback(
                iteraction, value)
            items.append(button)

        super().__init__(*items)
        self.question = question
        self.embed = embed
        self.value = None

    async def callback(self, interaction: discord.Interaction, value):
        self.disable_all_items()
        self.value = value
        self.stop()

    async def ask(self, ctx: discord.ApplicationContext) -> bool:
        message = await ctx.respond(content=self.question, embed=self.embed, view=self)
        await self.wait()
        await message.edit(view=None)
        return self.value
