import discord
import coc


class ClanSetupEmbed(discord.Embed):
    def __init__(self, clan: coc.Clan, fields: list[discord.EmbedField]):
        super().__init__(title="**__These are the settings for the clan setup__**",
                         description="Press a button to edit any of them. Click the Ok Button when you finished.", fields=fields)
        self.set_thumbnail(url=clan.badge.url)


class ClanSetup(discord.ui.View):
    def __init__(self, clan: coc.Clan, legend_players):
        self.rows = [
            {
                "field": discord.EmbedField(
                    name="Clan",
                    value=clan.name
                ),
                "value": None
            },
            {
                "field": discord.EmbedField(
                    name="Players",
                    value=f"{len(legend_players)} Legend League Players"
                ),
                "value": None
            },
            {
                "field": discord.EmbedField(name="a) Create a Group", value="None"),
                "value": True,
                "index": 0
            },
            {
                "field": discord.EmbedField(name="b) Create a Autoupdate Channel for the Group", value="None"),
                "value": True,
                "index": 1
            },
            {
                "field": discord.EmbedField(name="c) Create a Channel for each Player Autoupdate", value="None"),
                "value": False,
                "index": 2
            },
            {
                "field": discord.EmbedField(name="d) Create a Autopdate Channel for Global Leaderboard", value="None"),
                "value": True,
                "index": 3
            },
            {
                "field": discord.EmbedField(name="e) Create a Autoupdate Channel for Local Leaderboard", value="None"),
                "value": True,
                "index": 4
            }
        ]

        items = []
        for row in self.rows:
            if row["value"] is None:
                continue
            row["field"].value = row["value"]
            button = discord.ui.Button(
                label=row["field"].name[:2],
                style=discord.ButtonStyle.green if row["value"] else discord.ButtonStyle.red
            )
            button.callback = lambda iteraction, value=row: self.callback(
                iteraction, value)
            row["button"] = button
            row["field"].value = str(row["value"])
            items.append(button)
        ok_button = discord.ui.Button(
            label="Ok", style=discord.ButtonStyle.primary, row=1)
        ok_button.callback = self.on_finish
        super().__init__(ok_button, *items, timeout=600)

        self.embed = ClanSetupEmbed(
            clan, fields=[row["field"] for row in self.rows])
        self.canceled = True

    async def callback(self, interaction: discord.Interaction, row: dict):
        await interaction.response.defer()

        if row["index"] == 1 and not row["value"]:
            create_group_row = next(
                row for row in self.rows if "index" in row and row["index"] == 0)
            if not create_group_row["value"]:
                return

        row["value"] = not row["value"]
        row["button"].style = discord.ButtonStyle.green if row["value"] else discord.ButtonStyle.red
        row["field"].value = str(row["value"])
        if row["index"] == 0 and not row["value"]:
            autoupdate_group_row = next(
                row for row in self.rows if "index" in row and row["index"] == 1)
            if autoupdate_group_row["value"]:
                autoupdate_group_row["value"] = False
                autoupdate_group_row["button"].style = discord.ButtonStyle.red
                autoupdate_group_row["field"].value = str(False)

        await interaction.edit_original_response(embed=self.embed, view=self)

    async def on_finish(self, interaction: discord.Interaction):
        self.canceled = False
        self.stop()

    async def send(self, ctx: discord.ApplicationContext) -> bool:
        message = await ctx.respond(embed=self.embed, view=self)
        await self.wait()
        await message.edit(view=None)
        return self.canceled, [row["value"] for row in self.rows if "index" in row]
