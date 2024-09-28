import os
import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from db_setup import db, coll
from auto_update import start_member_count
# from riot_sync import syncOption
from commands import setup_commands

# Load token and channel ID from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')

# Bot setup
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    await start_member_count(bot)
    print(f"Logged in as {bot.user}")

# Setup commands
setup_commands(bot, SERVER_ID)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)
