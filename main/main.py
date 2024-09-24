import os
import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from discord import ApplicationContext
from discord.ui import Modal, InputText, Select, View

# 토큰 불러오기
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 봇 셋업
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

#라이엇 아이디 받기
class getID(Modal):
    def __init__(self):
        super().__init__(title="My Modal")
        self.add_item(InputText(label="닉네임:", placeholder="라이엇 닉네임을 입력해주세요"))
        self.add_item(InputText(label="# 태그:", placeholder="라이엇 게임태그를 입력해주세요"))

    async def callback(self, interaction: discord.Interaction):
        ID = self.children[0].value
        tag = self.children[1].value
        await interaction.response.send_message(f"라이엇 ID: {ID}#{tag}", ephemeral=True)

#계정연동 옵션
class syncOption(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="계정연동", description="새로운 라이엇 계정을 연동합니다", value="0"),
            discord.SelectOption(label="연동취소", description="연동된 계정을 해제합니다", value="1")
        ]
        super().__init__(placeholder="아래 옵션중 선택", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "0":
            riot = getID()
            await interaction.response.send_modal(riot)

# Create Slash Command group with bot.create_group
@bot.slash_command(name='sync', description='FUCKKKKKKKKKKKKKKK!!!')
async def sync(ctx: ApplicationContext):
    view = View()
    view.add_item(syncOption())
    await ctx.respond("Please select an option from the menu below:", view=view, ephemeral=True)

print("done")
# STEP 3: RUN BOT
bot.run(TOKEN)
