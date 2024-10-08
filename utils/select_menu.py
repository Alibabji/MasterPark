import discord
from discord.ui import Select
from utils.db_setup import warns_coll, alerts_coll
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
WARN_LOG_ID=int(os.getenv('WARN_LOG_ID'))

class AlertSelect(Select):
    def __init__(self, alerts, user, ctx):
        options = [
            discord.SelectOption(
                label=f"주의 {i + 1}",
                description=f"{self.format_date(a['date'])}: {a['reason']}"
            )
            for i, a in enumerate(alerts)
        ]
        super().__init__(placeholder="제거할 주의를 선택하세요", min_values=1, max_values=1, options=options)
        self.alerts = alerts
        self.user = user
        self.ctx = ctx

    def format_date(self, date):
        # Check if date is a string or a datetime object, and format accordingly
        if isinstance(date, datetime):
            return date.strftime('%Y-%m-%d %H:%M:%S')
        return date  # If it's a string, return as-is

    async def callback(self, interaction: discord.Interaction):
        selected_index = int(self.values[0].split()[1]) - 1
        removed_alert = self.alerts.pop(selected_index)
        alerts_coll.update_one(
            {"_id": {"server": self.ctx.guild.id, "user_id": self.user.id}},
            {"$set": {"count": len(self.alerts), "alerts": self.alerts}}
        )
        embed = discord.Embed(
            title=f"{self.user.display_name}님의 주의 제거됨",
            description=f"주의 #{selected_index + 1}이(가) 제거되었습니다.\n\n사유: {removed_alert['reason']}\n날짜: {self.format_date(removed_alert['date'])}"
        )
        await interaction.response.edit_message(embed=embed, view=None)

        # 로그 채널에 주의 제거 기록 추가
        log_embed = discord.Embed(
            title="⚠️ 유저 주의 제거됨",
            color=0x6846ff,
            timestamp=datetime.utcnow()
        )
        log_embed.add_field(name="유저", value=f"{self.user.mention} ({self.user.id})", inline=False)
        log_embed.add_field(name="관리자", value=f"{self.ctx.author.mention} ({self.ctx.author.id})", inline=False)
        log_embed.add_field(name="제거된 주의", value=f"#{selected_index + 1}", inline=False)
        log_embed.add_field(name="사유", value=removed_alert['reason'], inline=False)
        log_embed.add_field(name="날짜", value=self.format_date(removed_alert['date']), inline=False)

        log_channel = self.ctx.bot.get_channel(int(WARN_LOG_ID))  # WARN_LOG_ID는 로그 채널 ID로 대체
        if log_channel:
            await log_channel.send(embed=log_embed)


class WarningSelect(Select):
    def __init__(self, warnings, user, ctx):
        options = [
            discord.SelectOption(
                label=f"경고 {i + 1}",
                description=f"{self.format_date(w['date'])}: {w['reason']}"
            )
            for i, w in enumerate(warnings)
        ]
        super().__init__(placeholder="제거할 경고를 선택하세요", min_values=1, max_values=1, options=options)
        self.warnings = warnings
        self.user = user
        self.ctx = ctx

    def format_date(self, date):
        # Check if date is a string or a datetime object, and format accordingly
        if isinstance(date, datetime):
            return date.strftime('%Y-%m-%d %H:%M:%S')
        return date  # If it's a string, return as-is

    async def callback(self, interaction: discord.Interaction):
        selected_index = int(self.values[0].split()[1]) - 1
        removed_warning = self.warnings.pop(selected_index)
        warns_coll.update_one(
            {"_id": {"server": self.ctx.guild.id, "user_id": self.user.id}},
            {"$set": {"count": len(self.warnings), "warnings": self.warnings}}
        )
        embed = discord.Embed(
            title=f"{self.user.display_name}님의 경고 제거됨",
            description=f"경고 #{selected_index + 1}이(가) 제거되었습니다.\n\n사유: {removed_warning['reason']}\n날짜: {self.format_date(removed_warning['date'])}"
        )
        await interaction.response.edit_message(embed=embed, view=None)

        # 로그 채널에 경고 제거 기록 추가
        log_embed = discord.Embed(
            title="⚠️ 유저 경고 제거됨",
            color=0xa250ff,
            timestamp=datetime.utcnow()
        )
        log_embed.add_field(name="유저", value=f"{self.user.mention} ({self.user.id})", inline=False)
        log_embed.add_field(name="관리자", value=f"{self.ctx.author.mention} ({self.ctx.author.id})", inline=False)
        log_embed.add_field(name="제거된 경고", value=f"#{selected_index + 1}", inline=False)
        log_embed.add_field(name="사유", value=removed_warning['reason'], inline=False)
        log_embed.add_field(name="날짜", value=self.format_date(removed_warning['date']), inline=False)

        log_channel = self.ctx.bot.get_channel(int(WARN_LOG_ID))  # WARN_LOG_ID는 로그 채널 ID로 대체
        if log_channel:
            await log_channel.send(embed=log_embed)
