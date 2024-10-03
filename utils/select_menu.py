import discord
from discord.ui import Select
from MasterPark.utils.db_setup import warns_coll, alerts_coll
from datetime import datetime


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
