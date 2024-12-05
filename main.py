import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from features import auto_update
from features.auto_update import start_member_count
from functions.commands import setup_commands
from utils.logger import setup_logger
from utils.welcom import setup_welcomer

# Load token and channel ID from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True# Intents 설정을 먼저 하고

# functions.Bot 또는 discord.Bot 중 하나만 사용해야 합니다.
bot = commands.Bot(command_prefix="/", intents=intents)

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    await start_member_count(bot)
    print(f"Logged in as {bot.user}")

# Setup functions
setup_commands(bot, SERVER_ID)
setup_welcomer(bot)
setup_logger(bot)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
