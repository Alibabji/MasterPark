import os
import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from discord import ApplicationContext
from discord.ui import View
from auto_update import start_member_count
from riot_sync import syncOption

# Load token and channel ID from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Start the loop when the bot is ready
@bot.event
async def on_ready():
    await start_member_count(bot)
    print(f"Logged in as {bot.user}")

# Slash command for syncing
@bot.slash_command(name='sync', description='Sync your Riot account')
async def sync(ctx: ApplicationContext):
    view = View()
    view.add_item(syncOption())
    await ctx.respond("Please select an option from the menu below:", view=view, ephemeral=True)

print("done")
# Run the bot
bot.run(TOKEN)
