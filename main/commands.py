import discord
import pymongo.errors
from discord import ApplicationContext, Embed
from discord.ui import View
from datetime import datetime
import pytz
from db_setup import coll
# from riot_sync import syncOption
from warning_select import WarningSelect

def setup_commands(bot, SERVER_ID):

    '''
    @bot.slash_command(name='sync', description='Sync your Riot account')
    async def sync(ctx: ApplicationContext):
        view = View()
        view.add_item(syncOption())
        await ctx.respond("Please select an option from the menu below:", view=view, ephemeral=True)
    '''

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="warn", description="유저에게 경고를 줍니다.")
    async def warn(ctx, user: discord.Option(discord.Member, description="경고를 주고싶은 유저"), reason: discord.Option(str)):
        if ctx.author.guild_permissions.manage_guild:
            embed = discord.Embed(title="경고")
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_author(name=user.name, icon_url=avatar_url)
            embed.add_field(name="사유", value=reason)
            await ctx.respond(embed=embed)

            # Get the current time when the command is invoked (in UTC)
            current_time = datetime.utcnow()  # Get the current UTC time

            warning_data = {
                "_id": {"server": user.guild.id, "user_id": user.id},
                "count": 1,
                "warnings": [{
                    "date": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),  # Format the current time as a string
                    "reason": reason
                }]
            }

            try:
                coll.insert_one(warning_data)
            except pymongo.errors.DuplicateKeyError:
                coll.update_one(
                    {"_id": {"server": user.guild.id, "user_id": user.id}},
                    {"$inc": {"count": 1}, "$push": {"warnings": {"date": current_time, "reason": reason}}}
                )
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="warns", description="경고 기록을 확인합니다.")
    async def warns(
            ctx: ApplicationContext,
            user: discord.Option(discord.Member, description="경고 기록을 확인할 유저", required=False)
    ):
        # If no user is provided, default to the user who ran the command (both for admins and non-admins)
        if user is None:
            user = ctx.author

        # Fetch the warning data from the database
        warning_data = coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
        if warning_data:
            warning_count = warning_data.get("count", 0)
            warnings = warning_data.get("warnings", [])

            # Create the embed for displaying the warnings
            embed = discord.Embed(title="경고 기록")
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_author(name=user.name, icon_url=avatar_url)

            # Add warnings to the embed
            for warning in warnings:
                date = warning.get("date").strftime("%Y-%m-%d %H:%M:%S")
                reason = warning.get("reason", "사유 없음")
                embed.add_field(name=f"경고 날짜: {date}", value=f"사유: {reason}", inline=False)

            # If no warnings found
            if not warnings:
                embed.add_field(name="경고 기록", value="이 유저는 경고가 없습니다.", inline=False)
        else:
            embed = discord.Embed(
                title=f"{user.display_name}님의 경고 기록",
                description="이 유저는 경고가 없습니다."
            )

        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="removewarn", description="유저의 경고를 제거합니다.")
    async def removewarn(ctx: ApplicationContext, user: discord.Option(discord.Member, description="경고를 제거할 유저")):
        if ctx.author.guild_permissions.manage_guild:
            warning_data = coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
            if warning_data and warning_data.get("warnings"):
                warnings = warning_data.get("warnings", [])
                select_menu = WarningSelect(warnings=warnings, user=user, ctx=ctx)
                view = View()
                view.add_item(select_menu)
                await ctx.respond(f"{user.display_name}님의 경고 기록:", view=view, ephemeral=True)
            else:
                await ctx.respond("이 유저는 경고가 없습니다.", ephemeral=True)
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)
