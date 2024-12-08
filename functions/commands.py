from tkinter import Button

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
from utils.db_setup import warns_coll, bans_coll, alerts_coll
from utils.select_menu import WarningSelect, AlertSelect

load_dotenv()

banned_users = bans_coll
client = discord.Client()
ROLE_ID=int(os.getenv('SUBMOD_ID'))
WARN_LOG_ID=int(os.getenv('WARN_LOG_ID'))
TICKET_TEST_ID=int(os.getenv('TICKET_CHANNEL'))

class TicketView(View):
    def __init__(self, embed_message, max_slots, creator_id):
        super().__init__(timeout=86400)  # 24시간 (86400초) 동안 유지
        self.creator_id = creator_id # 작성자 id 저장
        self.embed_message = embed_message  # 메시지 객체 저장
        self.max_slots = max_slots  # 최대 인원수
        self.current_slots = 0  # 현재 참여 인원
        self.participants = []  # 참여자 리스트
        self.waitlists = [] # 대기자 리스트

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success)
    async def join_button(self, button: Button, interaction: discord.Interaction):
        print(self.current_slots)
        print(self.max_slots)

        user_id = interaction.user.id
        if user_id in self.participants or user_id in self.waitlists:
            await interaction.response.send_message("이미 참여하셨습니다!", ephemeral=True)
        else:
            embed = self.embed_message.embeds[0]
            if self.max_slots <= self.current_slots:
                self.waitlists.append(user_id)
                if self.max_slots == self.current_slots:
                    embed.add_field(name="대기자 목록", value=f"<@{user_id}>", inline=True)
                elif self.max_slots < self.current_slots:
                    embed.set_field_at(index=3, name="대기자 목록", value="\n".join([f"<@{uid}>" for uid in self.waitlists]), inline=True)
                await interaction.response.send_message("대기 참여 완료!", ephemeral=True)
                self.current_slots += 1
            else:
                self.participants.append(user_id)
                embed.set_field_at(index=2, name="참여자 목록", value="\n".join([f"<@{uid}>" for uid in self.participants]), inline=True)
                await interaction.response.send_message("참여 완료!", ephemeral=True)
                self.current_slots += 1
            embed.set_footer(text=f"남은 인원수: {0 if self.max_slots - self.current_slots < 0 else self.max_slots - self.current_slots}")
            await self.embed_message.edit(embed=embed)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button: Button, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in self.participants or user_id in self.waitlists:

            embed = self.embed_message.embeds[0]
            self.current_slots -= 1

            if user_id in self.waitlists:
                self.waitlists.remove(user_id)
                if not self.waitlists:
                    embed.remove_field(index=3)
                else:
                    embed.set_field_at(index=3, name="대기자 목록", value="\n".join([f"<@{uid}>" for uid in self.waitlists]), inline=True)

                await self.embed_message.edit(embed=embed)
                await interaction.response.send_message("대기 취소 완료!", ephemeral=True)

            elif user_id in self.participants:
                self.participants.remove(user_id)
                if self.waitlists:
                    self.participants.append(self.waitlists.pop(0))
                    embed.set_field_at(index=2, name="참여자 목록", value="\n".join([f"<@{uid}>" for uid in self.participants]), inline=True)

                    if not self.waitlists:
                        embed.remove_field(index=3)
                    else:
                        embed.set_field_at(index=3, name="대기자 목록", value="\n".join([f"<@{uid}>" for uid in self.waitlists]), inline=True)
                else:
                    if self.participants:
                        embed.set_field_at(index=2, name="참여자 목록", value="\n".join([f"<@{uid}>" for uid in self.participants]), inline=True)
                    else:
                        embed.set_field_at(index=2, name="참여자 목록", value="없음", inline=True)
                embed.set_footer(text=f"남은 인원수: {0 if self.max_slots - self.current_slots < 0 else self.max_slots - self.current_slots}")

            await self.embed_message.edit(embed=embed)
            await interaction.response.send_message("참여 취소 완료!", ephemeral=True)
        else:
            await interaction.response.send_message("참여하시지 않았습니다", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.primary)
    async def close_button(self, button: Button, interaction: discord.Interaction):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("이 버튼을 사용할 권한이 없습니다.", ephemeral=True)
            return

        # 모든 버튼 비활성화
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True

        # 임베드 업데이트
        embed = self.embed_message.embeds[0]
        embed.insert_field_at(index=0, name="모집이 마감되었습니다!", inline=False)

        await self.embed_message.edit(embed=embed, view=self)
        await interaction.response.send_message("모집이 마감되었습니다.", ephemeral=True)


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
            await ctx.respond("사유는 150자 이내여야 합니다!", ephemeral=True)  # Error if reason exceeds 150 characters
            return False
        return True

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="ticket", description="인원 모집 글을 생성합니다.")
    async def ticket(ctx, description: discord.Option(str), time: discord.Option(str, description=""), number: discord.Option(int)):

        embed = discord.Embed(title=f"<@{ctx.author.id}>님의 인원 모집", color=discord.Color.blue())
        embed.add_field(name="시간대", value=time, inline=False)
        embed.add_field(name="설명", value=description, inline=False)
        embed.add_field(name="참여자 목록", value="없음", inline=False)
        embed.set_image(url="https://i.ibb.co/Nn75mJ3/welcome-img.webp")
        embed.set_footer(text=f"남은 인원수: {number}")

        # 메시지 전송 및 버튼 추가
        message = await ctx.send(embed=embed)
        view = TicketView(embed_message=message, max_slots=number, creator_id=ctx.author.id)
        await message.edit(view=view)
        await ctx.response.send_message("글을 성공적으로 생성하였습니다!", ephemeral=True)

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

            log_embed = discord.Embed(
                title="🔔 유저 주의",
                color=0xFFB346,  # 색상 그대로 사용
                timestamp=current_time  # 슬래시 명령어에서 ctx.created_at 사용
            )
            log_embed.add_field(name="유저", value=f"{user.mention} ({user.id})", inline=False)
            log_embed.add_field(name="관리자", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
            log_embed.add_field(name="사유", value=reason, inline=False)
            log_embed.add_field(name="주의 수", value=str(warning_count), inline=True)

            log_channel = bot.get_channel(int(WARN_LOG_ID))
            if log_channel:
                await log_channel.send(embed=log_embed)
            else:
                print("WARN_LOG_ID로 로그 채널을 찾을 수 없습니다.")


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

            # 로그 임베드 추가
            log_embed = discord.Embed(
                title="⚠️ 유저 경고",
                color=0xFFD050,
                timestamp=current_time
            )
            log_embed.add_field(name="유저", value=f"{user.mention} ({user.id})", inline=False)
            log_embed.add_field(name="관리자", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
            log_embed.add_field(name="사유", value=reason, inline=False)
            log_embed.add_field(name="경고 수", value=str(warning_count), inline=True)

            log_channel = bot.get_channel(int(WARN_LOG_ID))
            if log_channel:
                await log_channel.send(embed=log_embed)
            else:
                print("WARN_LOG_ID로 로그 채널을 찾을 수 없습니다.")

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

            # 유저 추방 후 관리자에게 응답
            embed = discord.Embed(
                title=f"RIP {emoji_str}",
                description=f"{user.name}",
                color=discord.Colour.red()
            )
            embed.add_field(name="사유", value=reason)
            await ctx.respond(embed=embed)
            await user.ban(reason=reason)

            # MongoDB에 밴 정보 저장
            current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            ban_data = {
                "user_id": user.id,
                "user_name": user.name,
                "server_id": ctx.guild.id,
                "ban_time": current_time_str,
                "reason": reason
            }
            try:
                bans_coll.insert_one(ban_data)
                print(f"Ban data saved for {user.name}.")
            except Exception as e:
                print(f"Error saving ban data: {e}")

            # 로그 임베드 추가
            log_embed = discord.Embed(
                title="🚫 유저 밴",
                color=0xFF6962,
                timestamp=current_time
            )
            log_embed.add_field(name="유저", value=f"{user.mention} ({user.id})", inline=False)
            log_embed.add_field(name="관리자", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
            log_embed.add_field(name="사유", value=reason, inline=False)
            log_embed.add_field(name="밴 시간", value=current_time_str, inline=True)

            log_channel = bot.get_channel(int(WARN_LOG_ID))
            if log_channel:
                await log_channel.send(embed=log_embed)

        else:
            await ctx.respond("권한이 없습니다!", ephemeral=True)

    @bot.slash_command(guild_ids=[int(SERVER_ID)], name="unban", description="유저의 밴을 해제합니다.")
    async def unban(ctx, user_id: discord.Option(str, description="밴을 해제할 유저의 ID", required=True),
                    reason: discord.Option(str, description="밴 해제 사유", required=False)):
        current_time = datetime.utcnow()
        await ctx.defer(ephemeral=True)  # Allows for long-running operations
        if len(user_id) > 40:
            await ctx.respond("유효하지 않은 아이디 입니다.", ephemeral=True)
            return
        if reason is None or len(reason) > 150:
            await ctx.respond("사유는 150자 이내여야 합니다.", ephemeral=True)
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
            invite_link = await ctx.channel.create_invite(max_uses=1, unique=True)
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

            # MongoDB에서 밴 정보 삭제
            try:
                bans_coll.delete_one({"user_id": int(user_id), "server_id": ctx.guild.id})
                print(f"Ban data for {member.name} deleted from MongoDB.")
            except Exception as e:
                print(f"Error deleting ban data: {e}")

            # 로그 임베드 추가
            log_embed = discord.Embed(
                title="🟢 유저 언밴",
                color=0x62ff7f,
                timestamp=datetime.utcnow()
            )
            log_embed.add_field(name="유저 ID", value=f"{member.mention} ({user_id})", inline=False)
            log_embed.add_field(name="관리자", value=f"{ctx.author.mention} ({ctx.author.id})", inline=False)
            if reason:
                log_embed.add_field(name="사유", value=reason or "사유없음", inline=False)

            log_channel = bot.get_channel(int(WARN_LOG_ID))
            if log_channel:
                await log_channel.send(embed=log_embed)

        except discord.NotFound:
            await ctx.respond("해당 유저는 이미 언밴된 상태입니다.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("권한이 부족하여 밴을 해제할 수 없습니다.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"밴 해제 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

