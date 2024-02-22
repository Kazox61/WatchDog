import discord


class DropdownItem(discord.ui.Select):
    def __init__(self, place_holder, options: dict, min_values=1, max_values=1, ):
        options = [discord.SelectOption(label=label, value=value)
                   for label, value in options.items()]
        self.selected_options = []
        super().__init__(
            placeholder=place_holder,
            min_values=min_values,
            max_values=max_values,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()


class Dropdown(discord.ui.View):
    def __init__(self, place_holder: str, response: str, options: dict, min_values=1, max_values=1):
        self.dropdown = DropdownItem(
            place_holder, options, min_values, max_values)
        self.response = response
        super().__init__(self.dropdown)

    async def send(self, channel: discord.TextChannel):
        message = await channel.send(view=self)
        await self.wait()
        await message.edit(content=self.response.format(len(self.dropdown.values)), view=None)
        return self.dropdown.values
