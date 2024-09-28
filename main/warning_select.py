import discord
from discord.ui import Select
from db_setup import coll

class WarningSelect(Select):
    def __init__(self, warnings, user, ctx):
        options = [
            discord.SelectOption(label=f"경고 {i + 1}",
                                 description=f"{w['date'].strftime('%Y-%m-%d %H:%M:%S')}: {w['reason']}")
            for i, w in enumerate(warnings)
        ]
        super().__init__(placeholder="제거할 경고를 선택하세요", min_values=1, max_values=1, options=options)
        self.warnings = warnings
        self.user = user
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        selected_index = int(self.values[0].split()[1]) - 1
        removed_warning = self.warnings.pop(selected_index)
        coll.update_one(
            {"_id": {"server": self.ctx.guild.id, "user_id": self.user.id}},
            {"$set": {"count": len(self.warnings), "warnings": self.warnings}}
        )
        embed = discord.Embed(
            title=f"{self.user.display_name}님의 경고 제거됨",
            description=f"경고 #{selected_index + 1}이(가) 제거되었습니다.\n\n사유: {removed_warning['reason']}\n날짜: {removed_warning['date'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await interaction.response.edit_message(embed=embed, view=None)
