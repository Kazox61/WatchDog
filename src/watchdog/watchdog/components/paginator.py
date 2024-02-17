import discord
from abc import ABC, abstractmethod


class PaginatorBase(discord.ui.View, ABC):
    def __init__(self, embeds: list[discord.Embed], user_id: int = None):
        self.user_id = user_id
        self.current_embed_index = 0

        self.embeds: list[discord.Embed] = embeds

        self.top_button = discord.ui.Button(
            label='⏫', style=discord.ButtonStyle.green, disabled=True)
        self.top_button.callback = self.go_to_the_top
        self.previous_button = discord.ui.Button(
            label='🔼', style=discord.ButtonStyle.green, disabled=True)
        self.previous_button.callback = self.go_to_previous

        self.page_button = discord.ui.Button(label=f'Page {self.current_embed_index + 1}/{len(self.embeds)}',
                                             style=discord.ButtonStyle.gray, disabled=True)

        self.next_button = discord.ui.Button(
            label='🔽', style=discord.ButtonStyle.green)
        self.next_button.callback = self.go_to_next
        self.bottom_button = discord.ui.Button(label='⏬', style=discord.ButtonStyle.green,
                                               disabled=self.current_embed_index > len(self.embeds) - 3)
        self.bottom_button.callback = self.go_to_last
        super().__init__(self.top_button, self.previous_button, self.page_button,
                         self.next_button, self.bottom_button, timeout=300)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id is not None and self.user_id == interaction.user.id:
            return True
        if not interaction.user.bot:
            return True
        await interaction.response.send_message("Sorry, only the command user can use these buttons", ephemeral=True)
        return False

    async def go_to_the_top(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index = 0
        await self.update_view(interaction)

    async def go_to_previous(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index -= 1
        await self.update_view(interaction)

    async def go_to_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index += 1
        await self.update_view(interaction)

    async def go_to_last(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_embed_index = len(self.embeds) - 1
        await self.update_view(interaction)

    async def disable_buttons(self):
        self.top_button.disabled = self.current_embed_index < 2
        self.previous_button.disabled = self.current_embed_index < 1
        self.next_button.disabled = self.current_embed_index > len(
            self.embeds) - 2
        self.bottom_button.disabled = self.current_embed_index > len(
            self.embeds) - 3

    async def update_view(self, interaction: discord.Interaction):
        self.page_button.label = f'Page {self.current_embed_index + 1}/{len(self.embeds)}'
        await self.disable_buttons()
        await interaction.edit_original_response(embed=self.embeds[self.current_embed_index],
                                                 view=self if len(self.embeds) > 1 else None)

    @abstractmethod
    async def send(self, ctx: discord.ApplicationContext | discord.Interaction):
        pass


class PaginatorResponse(PaginatorBase):
    async def send(self, ctx: discord.ApplicationContext, ephemeral: bool = False):
        await self.disable_buttons()
        if len(self.embeds) > 1:
            message = await ctx.respond(embed=self.embeds[self.current_embed_index], view=self, ephemeral=ephemeral)
            await self.wait()
            await message.edit(view=None)
        else:
            await ctx.respond(embed=self.embeds[self.current_embed_index])


class PaginatorInteraction(PaginatorBase):
    async def send(self, ctx: discord.Interaction, ephemeral: bool = False):
        await self.disable_buttons()
        if len(self.embeds) > 1:
            message: discord.Interaction = await ctx.response.send_message(embed=self.embeds[self.current_embed_index], view=self, ephemeral=ephemeral)
            await self.wait()
            await message.edit_original_response(view=None)
        else:
            await ctx.response.send_message(embed=self.embeds[self.current_embed_index], ephemeral=ephemeral)
