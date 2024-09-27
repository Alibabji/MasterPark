import os
import discord
from discord.ext import tasks


async def start_member_count(bot):
    update_server_member.start(bot)

@tasks.loop(minutes=10)
async def update_server_member(bot):
    guild = bot.guilds[0]  # Assuming the bot is in one guild
    CHANNEL_ID=int(os.getenv('MEMBER_COUNT_ID'))
    channel = guild.get_channel(CHANNEL_ID)

    if channel and isinstance(channel, discord.VoiceChannel):
        # Fetch server member count (excluding bot)
        member_count = guild.member_count

        # Update channel name with member count
        new_name = f"전체멤버: {member_count}"
        await channel.edit(name=new_name)
        print(f"Updated channel name to '{new_name}'")