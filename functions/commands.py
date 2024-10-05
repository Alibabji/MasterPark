import discord
import pymongo.errors
from discord import ApplicationContext, Embed, Option
from discord.ui import View
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
from discord.ext import commands
from discord.utils import get
from MasterPark.utils.db_setup import warns_coll, bans_coll, alerts_coll
from MasterPark.utils.select_menu import WarningSelect, AlertSelect

load_dotenv()

banned_users = bans_coll
client = discord.Client()
ROLE_ID=int(os.getenv('SUBMOD_ID'))

def setup_commands(bot, SERVER_ID):

    # input check
    async def check_condition(ctx,user,reason):
        if not isinstance(user, discord.Member):  # Check if the user is a member of the guild
            await ctx.respond("서버에 존재하지 않는 멤버입니다!", ephemeral=True)
            return False
        elif ctx.author == user:
            await ctx.respond("자기자신에겐 사용 불가능한 명령어입니다!!", ephemeral=True)
            return False
        elif user.guild_permissions.manage_guild:
            await ctx.respond("관리자/봇에겐 사용 불가능한 명령어입니다!!", ephemeral=True)
            return False
        if len(reason) > 150:
            await ctx.respond("사유는 150자 이내여야 합니다.", ephemeral=True)  # Error if reason exceeds 150 characters
            return False
        return True

    @bot.slash_command(guild_ids=[int(SERVER_ID)],name="alert",description="유저에게 주의를 줍니다.")
    async def alert(ctx, user: discord.Option(discord.Member, description="경고를 주고싶은 유저"), reason: discord.Option(str)):
        if ctx.author.guild_permissions.manage_guild or ROLE_ID in [role.id for role in ctx.author.roles]:

            if not await check_condition(ctx,user,reason):
                return

            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            current_time = datetime.utcnow()

            alert_data = {
                "_id": {"server": user.guild.id, "user_id": user.id},
                "count": 1,
                "alerts": [{
                    "date": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "reason": reason,
                    "issued_by": ctx.author.display_name
                }]
            }
            try:
                alerts_coll.insert_one(alert_data) #DB에 데이터 저장
            except pymongo.errors.DuplicateKeyError:
                alerts_coll.update_one(
                    {"_id": {"server": user.guild.id, "user_id": user.id}},
                    {"$inc": {"count": 1}, "$push": {"alerts": {
                        "date": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "reason": reason,
                        "issued_by": ctx.author.display_name
                    }}}
                )

            await ctx.respond(f"{user.name}에게 주의를 주었습니다", ephemeral=True)

            user_alerts = alerts_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
            warning_count = user_alerts["count"] if user_alerts else 0

            #discord DM Embed
            embed = discord.Embed(
                title=f"📣 {ctx.author.name}께서 주의를 주셨습니다!",
                color=discord.Color.yellow()
            )
            embed.set_author(name=user.name,icon_url=avatar_url)
            embed.add_field(name="날짜",value = current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),inline=False)
            embed.add_field(name="사유", value=reason, inline=False)
            embed.add_field(name="현재 주의 수", value=str(warning_count), inline=False)

            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                await ctx.respond(f"{user.mention}님께 DM을 보낼 수 없습니다. (DM이 비활성화 되어있습니다.)", ephemeral=True)
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="alerts", description="주의 기록을 확인합니다.")
    async def alerts(ctx: ApplicationContext, user: discord.Option(discord.Member, description="주의 기록을 확인할 유저", required=False)):
        if user is None:
            user = ctx.author
            if user is None:
                await ctx.respond("유저 정보를 찾을 수 없습니다.", ephemeral=True)
                return
        elif user and not ctx.author.guild_permissions.manage_guild and ROLE_ID not in [role.id for role in ctx.author.roles]:
            await ctx.respond("권한이 없습니다!", ephemeral=True)
            return
        if user.bot:
            await ctx.respond("봇에게는 사용할 수 없습니다!", ephemeral=True)
            return

        current_time = datetime.utcnow()

        # Fetch the warning data from the database
        alert_data = alerts_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
        if alert_data:
            alert_count = alert_data.get("count", 0)
            alerts = alert_data.get("alerts", [])

            # Create the embed for displaying the alerts
            embed = discord.Embed(title="주의 기록")
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_author(name=user.name, icon_url=avatar_url)

            for alert in alerts:
                date = alert.get("date")
                reason = alert.get("reason", "사유 없음")
                embed.add_field(name=f"주의 날짜: {date}", value=f"사유: {reason}", inline=False)

            if not alerts:
                embed.add_field(name="주의 기록", value="이 유저는 주의가 없습니다.", inline=False)

        else:
            embed = discord.Embed(
                title=f"{user.display_name}님의 주의 기록",
                description="이 유저는 주의가 없습니다."
            )

        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="removealert", description="유저의 경고를 제거합니다.")
    async def removealert(ctx: ApplicationContext, user: discord.Option(discord.Member, description="주의를 제거할 유저")):
        if ctx.author.guild_permissions.manage_guild or ROLE_ID in [role.id for role in ctx.author.roles]:
            alert_data = alerts_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
            if alert_data and alert_data.get("alerts"):
                alerts = alert_data.get("alerts", [])
                select_menu = AlertSelect(alerts=alerts, user=user, ctx=ctx)
                view = View()
                view.add_item(select_menu)
                await ctx.respond(f"{user.display_name}님의 주의 기록:", view=view, ephemeral=True)
            else:
                await ctx.respond("이 유저는 주의가 없습니다.", ephemeral=True)
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="warn", description="유저에게 경고를 줍니다.")
    async def warn(ctx, user: discord.Option(discord.Member, description="경고를 주고싶은 유저"), reason: discord.Option(str)):
        if ctx.author.guild_permissions.manage_guild or ROLE_ID in [role.id for role in ctx.author.roles]:
            if not await check_condition(ctx, user, reason):
                return

            embed = discord.Embed(title="경고")
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_author(name=user.name, icon_url=avatar_url)
            embed.add_field(name="사유", value=reason)
            await ctx.respond(embed=embed)

            current_time = datetime.utcnow()

            # 경고 데이터 저장
            warning_data = {
                "_id": {"server": user.guild.id, "user_id": user.id},
                "count": 1,
                "warnings": [{
                    "date": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "expires_at": (current_time + timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "reason": reason,
                    "issued_by": ctx.author.display_name  # 경고를 준 관리자 정보 추가
                }]
            }

            try:
                warns_coll.insert_one(warning_data)
            except pymongo.errors.DuplicateKeyError:
                warns_coll.update_one(
                    {"_id": {"server": user.guild.id, "user_id": user.id}},
                    {"$inc": {"count": 1}, "$push": {"warnings": {
                        "date": current_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "expires_at": (current_time + timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "reason": reason,
                        "issued_by": ctx.author.display_name
                    }}}
                )

            # 경고 스택 조회
            user_warnings = warns_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
            warning_count = user_warnings["count"] if user_warnings else 0

            # 유저에게 상세한 DM 전송
            detailed_embed = discord.Embed(
                title="⚠️ 경고를 받았습니다!",
                description="아래 경고 정보를 확인해 주세요.",
                color=discord.Color.red()
            )
            detailed_embed.set_author(name=user.name, icon_url=avatar_url)
            detailed_embed.add_field(name="경고 날짜", value=current_time.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            detailed_embed.add_field(name="사유", value=reason, inline=False)
            detailed_embed.add_field(name="현재 경고 수", value=str(warning_count), inline=False)
            detailed_embed.add_field(name="경고한 관리자", value=ctx.author.display_name, inline=False)

            try:
                await user.send(embed=detailed_embed)
            except discord.Forbidden:
                await ctx.respond(f"{user.mention}님께 DM을 보낼 수 없습니다. (DM이 비활성화 되어있습니다.)", ephemeral=True)

            # 경고 4회 이상 시 자동 퇴장 처리
            if warning_count >= 4:
                await ban(ctx,user,"경고 누적")
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="warns", description="경고 기록을 확인합니다.")
    async def warns(ctx: ApplicationContext, user: discord.Option(discord.Member, description="경고 기록을 확인할 유저", required=False)):
        if user is None:
            user = ctx.author
            if user is None:
                await ctx.respond("유저 정보를 찾을 수 없습니다.", ephemeral=True)
                return
        elif user and not ctx.author.guild_permissions.manage_guild and ROLE_ID not in [role.id for role in ctx.author.roles]:
            await ctx.respond("권한이 없습니다!", ephemeral=True)
            return
        if user.bot:
            await ctx.respond("봇에게는 사용할 수 없습니다!", ephemeral=True)
            return

        current_time = datetime.utcnow()

        # Fetch the warning data from the database
        warning_data = warns_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
        if warning_data:
            warning_count = warning_data.get("count", 0)
            warnings = warning_data.get("warnings", [])

            # Create the embed for displaying the warnings
            embed = discord.Embed(title="경고 기록")
            avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
            embed.set_author(name=user.name, icon_url=avatar_url)

            # Check if the user running the command is the author or an admin
            is_admin = ctx.author.guild_permissions.manage_guild

            # Filter warnings based on expiration date
            active_warnings = []
            expired_warnings = []
            for warning in warnings:
                expires_at = datetime.strptime(warning.get("expires_at"), "%Y-%m-%d %H:%M:%S UTC")
                if current_time <= expires_at:
                    active_warnings.append(warning)
                else:
                    expired_warnings.append(warning)

            # Display active warnings if the user is not an admin
            if not is_admin:
                for warning in active_warnings:
                    date = warning.get("date")
                    reason = warning.get("reason", "사유 없음")
                    embed.add_field(name=f"경고 날짜: {date}", value=f"사유: {reason}", inline=False)

                if not active_warnings:
                    embed.add_field(name="경고 기록", value="이 유저는 활성화된 경고가 없습니다.", inline=False)

            # If the user is an admin, display both active and expired warnings
            if is_admin:
                for warning in warnings:
                    date = warning.get("date")
                    reason = warning.get("reason", "사유 없음")
                    expires_at = warning.get("expires_at")
                    embed.add_field(name=f"경고 날짜: {date} (만료일: {expires_at})", value=f"사유: {reason}", inline=False)

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
        if ctx.author.guild_permissions.manage_guild or ROLE_ID in [role.id for role in ctx.author.roles]:
            warning_data = warns_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
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

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="ban", description="유저를 밴합니다.")
    async def ban(ctx, user: discord.Option(discord.Member, description="밴하고 싶은 유저"), reason: discord.Option(str)):
        if ctx.author.guild_permissions.manage_guild:
            if not await check_condition(ctx, user, reason):
                return
            current_time = datetime.utcnow()
            emoji = get(ctx.guild.emojis, name="zany_face")  # Fetch the custom emoji

            # If emoji is found, convert it to its string format (e.g., <:emoji_name:emoji_id>)
            emoji_str = str(emoji) if emoji else "🤪"  # Fallback to a default emoji if not found

            user_alerts = alerts_coll.find_one({"_id": {"server": ctx.guild.id, "user_id": user.id}})
            warning_count = user_alerts["count"] if user_alerts else 0

            user_alerts = alerts_coll.find_one({"user_id": user.id})

            embed = discord.Embed(
                title="🫨 추방 당하셨습니다 🫨",
                color=discord.Color.red()
            )
            embed.add_field(name="날짜", value=current_time.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.add_field(name="사유", value=reason, inline=False)

            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                await ctx.respond(f"{user.mention}님께 DM을 보낼 수 없습니다. (DM이 비활성화 되어있습니다.)", ephemeral=True)

            embed = discord.Embed(
                title=f"RIP {emoji_str}",
                description=f"{user.name}",
                color=discord.Colour.red()
            )
            embed.add_field(name="사유", value=reason)
            await ctx.respond(embed=embed)
            await user.ban(reason=reason)

            # Save ban info to MongoDB
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            ban_data = {
                "user_id": user.id,
                "user_name": user.name,
                "server_id": ctx.guild.id,
                "ban_time": current_time,
                "reason": reason
            }
            try:
                bans_coll.insert_one(ban_data)
                print(f"Ban data saved for {user.name}.")
            except Exception as e:
                print(f"Error saving ban data: {e}")
        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="unban", description="유저의 밴을 해제합니다.")
    async def unban(ctx, user_id: discord.Option(str, description="밴을 해제할 유저의 ID", required=True), reason: discord.Option(str, description="밴 해제 사유", required=False)):
        await ctx.defer(ephemeral=True)  # Allows for long-running operations
        if len(user_id) > 40:
            await ctx.respond("유효하지 않은 아이디 입니다.", ephemeral=True)  # Error if reason exceeds 150 characters
            return
        if reason is None or len(reason) > 150:
            await ctx.respond("사유는 150자 이내여야 합니다.", ephemeral=True)  # Error if reason exceeds 150 characters
            return
        # Fetch the user by their ID
        try:
            member = await bot.get_or_fetch_user(user_id)
        except discord.NotFound:
            await ctx.respond("해당 유저를 찾을 수 없습니다.", ephemeral=True)
            return

        # Unban the user
        try:
            await ctx.guild.unban(member)
            await ctx.respond(f"{member.mention}님을 언밴했습니다.", ephemeral=True)

            # Send a Direct Message to the unbanned user
            invite_link = await ctx.channel.create_invite(max_uses=1, unique=True)  # Generate an invite link
            embed = discord.Embed(
                title="🚪 서버로 다시 오실 수 있습니다!",
                description="밴이 해제되었습니다. 아래 초대 링크를 사용하여 서버에 다시 참여하세요.",
                color=discord.Color.green()
            )
            embed.add_field(name="서버 초대 링크", value=invite_link.url, inline=False)
            if reason:
                embed.add_field(name="밴 해제 사유", value=reason, inline=False)

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                await ctx.respond(f"{member.mention}님께 DM을 보낼 수 없습니다. (DM이 비활성화 되어있습니다.)", ephemeral=True)

            # Remove the ban data from MongoDB
            try:
                bans_coll.delete_one({"user_id": int(user_id), "server_id": ctx.guild.id})
                print(f"Ban data for {member.name} deleted from MongoDB.")
            except Exception as e:
                print(f"Error deleting ban data: {e}")

        except discord.NotFound:
            await ctx.respond("해당 유저는 이미 언밴된 상태입니다.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("권한이 부족하여 밴을 해제할 수 없습니다.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"밴 해제 중 오류가 발생했습니다: {str(e)}", ephemeral=True)
