from fileinput import close

import discord
from attr.validators import max_len
from discord.ext import commands
from discord.ui import Button, View, Select, modal, Modal, InputText
from dotenv import load_dotenv
import os
import asyncio
import subprocess

load_dotenv()
TICKET_CHANNEL = int(os.getenv("TICKET_CHANNEL"))
ADMIN = int(os.getenv("MOD_ID"))

class TicketModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="티켓생성")

        self.add_item(discord.ui.InputText(
            label="티켓제목",
            placeholder="티켓 설명/주제을 입력해주세요",
            style=discord.InputTextStyle.short
        ))
        self.add_item(discord.ui.InputText(
            label="티켓내용",
            placeholder="티켓 내용을 입력해주세요 (필수)",
            max_length=500,
            style=discord.InputTextStyle.long
        ))

    async def callback(self, interaction:discord.Interaction):
        title = self.children[0].value
        content=self.children[1].value

        guild=interaction.guild
        if guild:
            category = discord.utils.get(guild.categories, name="ticket")
            if category:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True)
                }
                ticket_channel=await guild.create_text_channel(
                    name="🎫-ticket",
                    topic=f"박사범의 롤려차기 티켓채널입니다. 도움을 위해 <@&{ADMIN}>에게 연락하세요",
                    overwrites=overwrites,
                    category=category
                )

                embed = discord.Embed(
                    title="티켓 생성됨",
                    description=f"{interaction.user.mention}님 안녕하세요!"
                )
                embed.add_field(name="",value="관리자가 곧 도와드릴 겁니다")
                embed.add_field(name="제목",value=title, inline=False)
                embed.add_field(name="내용",value=content, inline=False)

                ticket_close = Button(label="닫기", style=discord.ButtonStyle.red,emoji="🔒")

                select= Select(options=[
                discord.SelectOption(
                    label="유저 추가",
                    description="현 티켓 채널에 유저를 추가합니다",
                    emoji="👥"),
                discord.SelectOption(
                    label="유저 제거",
                    description="현 티켓 채널에 유저를 제거합니다",
                    emoji="❌")
                ])

                async def ticket_close_callback(interaction: discord.Interaction):
                    close_embed = discord.Embed(
                        title="티켓 닫기",
                        description="`10`초 후에 티켓이 닫힙니다... ⏳"
                    )
                    close_embed.add_field(name="", value="*닫히지 않을시 관리자에게 문의해주세요!*")

                    await interaction.response.send_message(embed=close_embed)

                    await asyncio.sleep(10)
                    log_dir = os.path.join("log")
                    if not os.path.exists(log_dir):
                        os.makedirs(log_dir)
                    # Use DiscordChatExporter to export chat
                    output_file = os.path.join(log_dir, f"{ticket_channel.id}_chat_log.html")  # Define the output file name
                    try:
                        # Ensure DiscordChatExporter is set up correctly in the system path or provide the full path
                        subprocess.run(
                            [
                                "C:\\Users\\woodz\\Downloads\\DiscordChatExporter.Cli.win-x64\\DiscordChatExporter.CLI.exe",
                                # Updated path
                                "export",
                                "-t", os.getenv("DISCORD_TOKEN"),  # Ensure DISCORD_TOKEN is set in your .env file
                                "-c", str(ticket_channel.id),  # Channel ID to export
                                "-f", "HtmlDark",  # Export format (you can change this if needed)
                                "-o", output_file  # Output file path
                            ],
                            check=True
                        )

                    except subprocess.CalledProcessError as e:
                        error_embed = discord.Embed(
                            title="티켓 로그 내보내기 실패",
                            description="티켓 채널 로그를 내보내는 도중 오류가 발생했습니다.",
                            color=discord.Color.red()
                        )
                        await interaction.followup.send(embed=error_embed)
                        return

                    # Send the exported chat file to the specified channel
                    log_channel = interaction.guild.get_channel(1317719542360834100)  # Replace with your target channel ID
                    if log_channel:
                        with open(output_file, "rb") as file:
                            await log_channel.send(file=discord.File(file, filename=f"{ticket_channel.id}_chat_log.html"))

                    # Finally, delete the ticket channel
                    await ticket_channel.delete()

                ticket_close.callback = ticket_close_callback





                view = View()
                view.add_item(select)
                view.add_item(ticket_close)
                await ticket_channel.send(f"<@{interaction.user.id}>님이 티켓을 생성하였습니다 | <@&{ADMIN}>", embed=embed, view=view)

                await interaction.response.send_message(
                    content=f"티켓 채널 생성에 성공하였습니다! > **<#{ticket_channel.id}>**",
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                content="티켓 채널 생성의 실패했습니다",
                ephemeral=True
            )

async def handle_report(interaction: discord.Interaction):
    print("hi")

async def handle_ticket_creation(interaction: discord.Interaction):
    modal = TicketModal()
    await interaction.response.send_modal(modal)

async def ticket_options(interaction):
    ticket_option = Select(options=[
        discord.SelectOption(label="신고하기", emoji="🚨"),
        discord.SelectOption(label="티켓생성", emoji="🎫")
    ])

    async def select_callback(interaction: discord.Interaction):
        if ticket_option.values[0] == "신고하기":
            await handle_report(interaction)
        elif ticket_option.values[0] == "티켓생성":
            await handle_ticket_creation(interaction)

    ticket_option.callback = select_callback

    ticket_embed = discord.Embed(
        title="티켓 생성하기",
        description="티켓 종류를 선택해주세요",
        color=0xf8ba00
    )

    view=View()
    view.add_item(ticket_option)
    await interaction.response.send_message(embed=ticket_embed, view=view, ephemeral=True)


async def ticket_send(bot):
    channel = bot.get_channel(TICKET_CHANNEL)
    embed = discord.Embed(
        title="건의/신고 티켓 생성",
        description="건의 채널 생성시엔 '건의'를, 신고시엔 '신고'를 눌러주세요",
        color=0xf8ba00

    )
    ticket = Button(label="티켓 생성",style=discord.ButtonStyle.primary, emoji="📨")

    async def ticket_callback(interaction: discord.Interaction):
        await ticket_options(interaction)

    ticket.callback = ticket_callback

    view = View()
    view.add_item(ticket)

    await channel.send(embed=embed, view=view)