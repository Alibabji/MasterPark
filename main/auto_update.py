import os
import discord
from discord.ext import tasks

intents = discord.Intents.default()
intents.members = True  # 멤버 정보에 접근하려면 필수
intents.guilds = True

async def start_member_count(bot):
    update_server_member.start(bot)

@tasks.loop(minutes=10)
async def update_server_member(bot):
    guild = bot.guilds[0]  # Assuming the bot is in one guild
    CHANNEL_ID = int(os.getenv('MEMBER_COUNT_ID'))
    channel = guild.get_channel(CHANNEL_ID)

    if channel and isinstance(channel, discord.VoiceChannel):
        # Fetch server member count (excluding bot)
        members = guild.fetch_members(limit=None)  # 최신 멤버 목록을 가져옴
        member_count = guild.member_count

        # Update channel name with member count
        new_name = f"전체 멤버: {member_count}"
        await channel.edit(name=new_name)
        print(f"Updated channel name to '{new_name}'")

    # 인증인원 업데이트
    ROLE_ID = 1289797945910231110  # Role ID
    ROLE_CHANNEL_ID = 1289798589727506452  # 통방 ID
    role = guild.get_role(ROLE_ID)
    role_channel_new_name = f"정식 멤버: {len(role.members)}"
    channel = bot.get_channel(ROLE_CHANNEL_ID)
    await channel.edit(name=role_channel_new_name)
    print(f"Updated approved channel name to '{role_channel_new_name}'")
