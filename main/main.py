import os
import discord
from discord import Intents
from discord.ext import commands, tasks
from dotenv import load_dotenv
from discord import ApplicationContext
from discord.ui import Modal, InputText, Select, View

# Load token and channel ID from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('MEMBER_COUNT_ID'))  # Convert CHANNEL_ID to an integer

# Bot setup
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    update_server_member.start()
    print(f"Logged in as {bot.user}")

@tasks.loop(seconds=1)
async def update_server_member():
    guild = bot.guilds[0]  # Assuming the bot is in one guild
    channel = guild.get_channel(CHANNEL_ID)
    if channel and isinstance(channel, discord.VoiceChannel):
        # Fetch server member count
        member_count = guild.member_count

        # Update channel name with member count
        new_name = f"전체멤버 - {member_count}"
        await channel.edit(name=new_name)
        print(f"Updated channel name to '{new_name}'")

# Modal to get Riot ID
class getID(Modal):
    def __init__(self):
        super().__init__(title="My Modal")
        self.add_item(InputText(label="닉네임:", placeholder="라이엇 닉네임을 입력해주세요"))
        self.add_item(InputText(label="# 태그:", placeholder="라이엇 게임태그를 입력해주세요"))

    async def callback(self, interaction: discord.Interaction):
        ID = self.children[0].value
        tag = self.children[1].value
        await interaction.response.send_message(f"라이엇 ID: {ID}#{tag}", ephemeral=True)

# Select menu for account sync option
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

# Slash command for syncing
@bot.slash_command(name='sync', description='Sync your Riot account')
async def sync(ctx: ApplicationContext):
    view = View()
    view.add_item(syncOption())
    await ctx.respond("Please select an option from the menu below:", view=view, ephemeral=True)

print("done")
# Run the bot
bot.run(TOKEN)
