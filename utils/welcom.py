import discord
from dotenv import load_dotenv
import os

from .utils import Util

load_dotenv()

WELCOME_LOG_ID=int(os.getenv('WELCOME_MESSAGE'))
GENERAL_ID=int(os.getenv('GENERAL_CHANNEL'))

def setup_welcomer(bot):
    @bot.event
    async def on_member_join(member):

        welcome_channel = bot.get_channel(WELCOME_LOG_ID)
        general_channel = bot.get_channel(GENERAL_ID)
        name = member.display_name
        icon = member.display_avatar

        embed = discord.Embed(
            title=f"관원님, 반갑습니다~",
            description=f'''<@{member.id}>님 기합소리 낼 준비 되셨나요?
             
             준비 되셨다면 {general_channel.mention} 에 가서 규칙 읽고 인증마크를 누르고 기합소리를 내어 롤려차기를 배우러 가봅시다!''',
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=f"{icon}")
        embed.set_image(url="https://i.ibb.co/Nn75mJ3/welcome-img.webp")
        await welcome_channel.send(embed=embed)