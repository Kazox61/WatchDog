import discord
from discord.ext import commands
import asyncio
import coc
from bson.objectid import ObjectId

from shared.coc_utils import get_current_insertion_date

from watchdog.custom_bot import CustomBot
from watchdog.components import PlayerTablePaginatorResponse, PlayerOverviewEmbed, PaginatorResponse, PlayerTableEmbed
from watchdog.autocomplete import search_group_user, parse_group_user, search_group, parse_group, search_player, parse_player, search_location, locations


def sort_by_current_trophies(element):
    if not element:
        return 0
    return element["trophies"]


def sort_by_day_start_trophies(element):
    try:
        battle_log = element["battle_log"][get_current_insertion_date()]
        try:
            day_start_trophies = battle_log["reset_trophies"]
        except KeyError:
            attacks = battle_log.get(
                "attacks") if battle_log.get("attacks") else []
            defenses = battle_log.get(
                "defenses") if battle_log.get("defenses") else []
            day_start_trophies = element["trophies"] + \
                sum(attacks) + sum(defenses)
        return day_start_trophies
    except KeyError:
        return 0


def sort_by_trophies_delta(element):
    try:
        battle_log = element["battle_log"][get_current_insertion_date()]
    except KeyError:
        return 0
    try:
        sum_attacks = sum(battle_log['attacks'])
    except KeyError:
        sum_attacks = 0
    try:
        sum_defenses = sum(battle_log['defenses'])
    except KeyError:
        sum_defenses = 0
    return sum_attacks + sum_defenses


class Group(commands.Cog):
    group = discord.SlashCommandGroup("group", "All Group commands")
    group_add = group.create_subgroup("add", "All Group Add commands")
    group_remove = group.create_subgroup("remove", "All Group Add commands")

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @group.command(name="create", description="Create a group where you can store multiple players and get updates in a liveticker channel.")
    @discord.option("visibility", description="Choose the visbility", choices=["Public", "Private"])
    async def group_create(self,
                           ctx: discord.ApplicationContext,
                           name: str,
                           visibility: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        public = visibility == "Public"
        result = await self.bot.group_db.find_one({
            "name": name
        })
        if result is None:
            await self.bot.group_db.insert_one({
                "owner_id": ctx.user.id,
                "name": name,
                "public": public,
                "search_count": 0,
                "members": [ctx.user.id],
                "players": []
            })
            await ctx.respond(f"Successfully created group `{name}`. You can add now members to `{name}`.")
        else:
            await ctx.respond(f"You have already a group named `{name}`. Try it again with a different name.")

    @group.command(name="delete", description="Delete a group permanently if you are owner of the group.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_delete(self,
                           ctx: discord.ApplicationContext,
                           group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to delete Group.")
            return

        success = await self.bot.group_db.delete_one(
            {"_id": ObjectId(selected_group["id"])})
        await ctx.respond(
            f"Successfully deleted `{selected_group['name']}`"
            if success else
            f"Failed to delete `{selected_group['name']}`. You are not owner of the group."
        )

    @group.command(name="visibility", description="Set the visibility of the group to private to hide them from non members.")
    @discord.commands.option("name", description="Choose your group", autocomplete=search_group_user)
    @discord.commands.option("visibility", description="Choose the visbility", choices=["Public", "Private"])
    async def group_visibility(self,
                               ctx: discord.ApplicationContext,
                               name: str,
                               visibility: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        public = visibility == "Public"
        selected_group = await parse_group_user(name, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to set visibility to `{visibility}`.")
            return

        if selected_group["public"] == public:
            await ctx.respond(f"Visibility already `{visibility}`.")
            return

        result = await self.bot.group_db.update_one({"_id": ObjectId(selected_group["id"])},
                                                    {"$set": {"public": public}})
        success = result.modified_count > 0
        await ctx.respond(
            f"Visibility set to `{visibility}` for `{selected_group['name']}`"
            if success else
            f"Failed to set visibility to `{visibility}` for `{selected_group['name']}`.")

    @group.command(name="rename", description="Rename the group to a unique name.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    @discord.commands.option("name", description="Type your new group name")
    async def group_rename(self,
                           ctx: discord.ApplicationContext,
                           group: str,
                           name: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to rename Group to `{name}`.")
            return

        if selected_group["name"] == name:
            await ctx.respond(f"`{name}` is already the group name.")
            return

        result = await self.bot.group_db.find_one({"name": name})
        if result is None:
            result = await self.bot.group_db.update_one({"_id": ObjectId(selected_group["id"])}, {
                "$set": {'name': name}})
            if result.modified_count > 0:
                await ctx.respond(f"Renamed group to `{name}`.")
                return
        await ctx.respond(f"Failed to rename `{selected_group['name']}` to `{name}`. `{name}` is already taken.")

    @group_add.command(name="member", description="Add a discord user to your group, so he can see the private group and manage players.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_add_member(self,
                               ctx: discord.ApplicationContext,
                               group: str,
                               user: discord.User):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to add {user.name} to the Group.")
            return

        await self.bot.try_create_user(user.id)

        result = await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"])}, {"$addToSet": {'members': user.id}})

        await ctx.respond(
            f"`{user.display_name}` succussfully added to the group."
            if result.modified_count > 0 else
            f"`{user.display_name}` is already member of the group.")

    @group_remove.command(name="member", description="Remove a discord user from your group.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_remove_member(self,
                                  ctx: discord.ApplicationContext,
                                  group: str,
                                  user: discord.User):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to remove {user.name} from the Group.")
            return

        result = await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"]),
             "owner_id": {"$ne": user.id}},
            {"$pull": {"members": user.id}})
        await ctx.respond(
            f"`{user.display_name}` succussfully removed from the group."
            if result.modified_count > 0 else
            f"`{user.display_name}` is owner or not a member of the group.")

    @group_add.command(name="player", description="Add a player to your group's player list.")
    @discord.commands.option("group", description="Choose the group", autocomplete=search_group_user)
    @discord.commands.option("player", description="Choose the player", autocomplete=search_player)
    async def group_add_player(
        self,
        ctx: discord.ApplicationContext,
        group: str,
        player: str
    ):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)
        selected_group = await parse_group_user(group, ctx.user.id)

        if selected_group is None:
            await ctx.respond("Failed to add Player to the Group.")
            return

        player_tag = parse_player(player)
        success = await self.try_add_player_to_group(selected_group["id"], player_tag)
        await ctx.respond(f"Added `{player_tag}` to `{selected_group['name']}`." if success else f"Failed to add `{player_tag}` to `{selected_group['name']}`.")

    @group_remove.command(name="player", description="Remove a player from your group's player list.")
    @discord.commands.option("group", description="Choose the group", autocomplete=search_group_user)
    @discord.commands.option("player", description="Choose the player", autocomplete=search_player)
    async def group_remove_player(
        self,
        ctx: discord.ApplicationContext,
        group: str,
        player: str
    ):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)
        selected_group = await parse_group_user(group, ctx.user.id)

        if selected_group is None:
            await ctx.respond("Failed to remove Player from the Group.")
            return

        player_tag = parse_player(player)
        result = await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"]), "members": ctx.user.id},
            {"$pull": {"players": player_tag}})
        await ctx.respond(f"Removed `{player_tag}` from `{selected_group['name']}`."
                          if result.modified_count > 0 else
                          f"Failed to remove `{player_tag}` from `{selected_group['name']}`.")

    @group_add.command(name="notifications", description="Choose the group from which you want to get notifications in your DM.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_add_notifications(self,
                                      ctx: discord.ApplicationContext,
                                      group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to add notifications.")
            return

        result = await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"])},
            {"$addToSet": {'notifications': ctx.user.id}})

        await ctx.respond(
            f"You succussfully added notifications for `{selected_group['name']}`."
            if result.modified_count > 0 else
            f"Failed to add notifications for `{selected_group['name']}`.")

    @group_remove.command(name="notifications", description="Choose the group from which you don't want to get notifications in your DM.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_remove_notifications(self,
                                         ctx: discord.ApplicationContext,
                                         group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to remove notifications.")
            return

        result = await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"])},
            {"$pull": {'notifications': ctx.user.id}})

        await ctx.respond(
            f"You succussfully removed notifications for `{selected_group['name']}`."
            if result.modified_count > 0 else
            f"Failed to remove notifications for `{selected_group['name']}`.")

    @group_add.command(name="autoupdate", description="Add Autoupdate for your group.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_add_autoupdate(self,
                                   ctx: discord.ApplicationContext,
                                   group: str,
                                   channel: discord.TextChannel):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond("Failed to add Autoupdate for the Group.")
            return

        message = await channel.send("Loading...")

        result = await self.bot.group_db.update_one({"_id": ObjectId(selected_group["id"]), "autoupdate": {"$not": {"$elemMatch": {"channel_id":  channel.id}}}},
                                                    {"$addToSet": {"autoupdate": {"channel_id": channel.id, "message_id": message.id}}})

        await ctx.respond(
            f"Successfully added Autoupdate for `{selected_group['name']}` to {channel.mention}."
            if result.modified_count > 0 else
            f"Failed to add Autoupdate for `{selected_group['name']}` to `{channel.mention}`")

    @group_add.command(name="leaderboard", description="Add players from the leaderboard to your group.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    @discord.commands.option("location", description="Choose the location", autocomplete=search_location)
    @discord.commands.option("limit", description="Choose the limit")
    async def group_add_leaderboard(self,
                                    ctx: discord.ApplicationContext,
                                    group: str,
                                    location: str,
                                    limit: int):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond("Failed to add Leaderboard Players to the Group.")
            return

        country_number = locations[location]
        players = await self.bot.coc_client.get_location_players(country_number, limit=limit)

        player_tasks = []
        i = 0
        for player in players:
            task = asyncio.ensure_future(
                self.try_add_player_to_group(selected_group["id"], player.tag))
            player_tasks.append(task)
        responses = await asyncio.gather(*player_tasks, return_exceptions=True)
        for success in responses:
            if success:
                i += 1
        await ctx.respond(f"Added `{str(i)}/{str(limit)}` Players from Leaderboard `{location}` to `{selected_group['name']}`.")

    @group.command(name="leave", description="Choose the group which you'd like to leave.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_leave(self,
                          ctx: discord.ApplicationContext,
                          group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond("Failed to leave the Group.")
            return

        result = self.group_collection.update_one(
            {"_id": ObjectId(selected_group["id"]),
             "owner_id": {"$ne": ctx.user.id}},
            {"$pull": {"members": ctx.user.id}})
        await ctx.respond("Successfully left the group."
                          if result.modified_count > 0 else
                          "You are not in the group or you are owner of the group.")

    @group.command(name="liveticker", description="Choose the channel where you'd like to receive updates.")
    @discord.commands.option("group", description="Choose your group", autocomplete=search_group_user)
    async def group_liveticker(self,
                               ctx: discord.ApplicationContext,
                               group: str,
                               channel: discord.TextChannel):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond(f"Failed to set Liveticker to {channel.mention}.")
            return

        await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"])}, {"$set": {"channel_id": channel.id}})
        await ctx.respond(f"Successfully set the liveticker to {channel.mention}.")

    @group.command(name="search", description="Search for a public group to see the overview stats.")
    @discord.commands.option("group", description="Choose the group", autocomplete=search_group)
    async def group_search(self,
                           ctx: discord.ApplicationContext,
                           group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group(group)

        result = await self.bot.group_db.find_one(
            {"_id": ObjectId(selected_group["id"])})

        if result is None:
            await ctx.respond("Group doesn't exist or there are no players in the group.")
            return

        players = []

        await self.bot.group_db.update_one(
            {"_id": ObjectId(selected_group["id"])},
            {"$inc": {"search_count": 1}}
        )

        players = await self.bot.get_players(result["players"])
        players.sort(key=sort_by_current_trophies, reverse=True)

        if players == []:
            await ctx.respond("Group doesn't exist or there are no players in the group.")
            return

        paginator = PlayerTablePaginatorResponse(
            f"Group players `{selected_group['name']}`",
            players
        )
        await paginator.send(ctx)

    @group.command(name="check", description="Check the overview stats for a group where you are a member of.")
    @discord.commands.option("group", description="Choose the group", autocomplete=search_group_user)
    async def group_check(self,
                          ctx: discord.ApplicationContext,
                          group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond("Failed to check the Group.")
            return

        result = await self.bot.group_db.find_one(
            {"_id": ObjectId(selected_group["id"])})

        if result is None:
            await ctx.respond("Group doesn't exist or there are no players in the group.")
            return

        players = await self.bot.get_players(result["players"])
        players.sort(key=sort_by_current_trophies, reverse=True)
        paginator = PlayerTablePaginatorResponse(
            f"Group players",
            players
        )
        await paginator.send(ctx)

    @group.command(name="stats", description="Get the individual stats for each player in the group.")
    @discord.commands.option("group", description="Choose the group", autocomplete=search_group_user)
    async def group_stats(self,
                          ctx: discord.ApplicationContext,
                          group: str):
        await ctx.defer()
        await self.bot.try_create_user(ctx.user.id)

        selected_group = await parse_group_user(group, ctx.user.id)
        if selected_group is None:
            await ctx.respond("Failed to find the Group.")
            return

        result = await self.bot.group_db.find_one(
            {"_id": ObjectId(selected_group["id"])})

        if result is None:
            await ctx.respond("Group doesn't exist or there are no players in the group.")
            return
        embeds = []
        for player_tag in result["players"]:
            player = await self.bot.get_player(player_tag)
            embed = PlayerOverviewEmbed(player)
            embeds.append(embed)

        paginator = PaginatorResponse(embeds)
        await paginator.send(ctx)

    async def try_add_player_to_group(self, group_id, player_tag) -> bool:
        try:
            player = await self.bot.coc_client.get_player(player_tag)
            count = await self.bot.player_db.count_documents({'tag': player_tag})
            if count == 0:
                await self.bot.player_db.insert_one(
                    {'tag': player_tag, 'name': player.name, 'trophies': player.trophies, 'attack_wins': player.attack_wins,
                     'defense_wins': player.defense_wins,
                     'battle_log': {get_current_insertion_date(): {'attacks': [], 'defenses': [], 'reset_trophies': player.trophies}}})

            result = await self.bot.group_db.update_one(
                {"_id": ObjectId(group_id)},
                {"$addToSet": {"players": player_tag}})
            return result.modified_count > 0
        except coc.NotFound:
            return False
        except coc.Maintenance:
            return False


def setup(bot):
    bot.add_cog(Group(bot))
