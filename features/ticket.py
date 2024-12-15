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
ROLE_ID=int(os.getenv('SUBMOD_ID'))

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
                ticket_channel = await guild.create_text_channel(
                    name="🎫-ticket",
                    topic=f"박사범의 롤려차기 티켓채널입니다. 도움을 위해 <@&{ADMIN}>에게 연락하세요 (creator_id:{interaction.user.id})",
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
                    creator_id = None
                    if interaction.channel.topic:
                        try:
                            creator_id = int(interaction.channel.topic.split("creator_id:")[-1].strip(")"))
                        except (ValueError, IndexError):
                            pass  # ID가 없거나 잘못된 경우 대비

                    # 권한 확인: 티켓 생성자이거나 관리 권한이 있는 경우만 허용
                    if not (
                            interaction.user.id == creator_id  # 티켓 생성자인 경우
                            or interaction.user.guild_permissions.manage_guild  # 서버 관리 권한이 있는 경우
                    ):
                        await interaction.response.send_message(
                            content="❌ 티켓을 닫을 권한이 없습니다. 관리자에게 문의해주세요!",
                            ephemeral=True
                        )
                        return  # 권한 부족 시 종료

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

                async def select_callback(interaction: discord.Interaction):
                    # Ensure the user is an admin before allowing the action
                    if not (interaction.user.guild_permissions.manage_guild or ROLE_ID in [role.id for role in interaction.user.roles]):
                        await interaction.response.send_message(
                            content="유저를 추가할 권한이 없습니다!\n관리자에게 부탁해주세요",
                            ephemeral=True  # This makes the message visible only to the user who clicked
                        )
                        return  # Exit the function early, preventing further actions
                    await interaction.response.defer()  # 응답 예약 (작업 중 표시)

                    if select.values[0] == "유저 추가":
                        members = [member for member in interaction.guild.members if not member.bot]

                        # 유저 목록을 25명씩 분할
                        chunks = [members[i:i + 25] for i in range(0, len(members), 25)]

                        # 선택 뷰를 생성하는 함수
                        async def create_member_selection_view(chunk_index=0):
                            chunk = chunks[chunk_index]
                            options = [
                                discord.SelectOption(
                                    label=member.display_name,
                                    value=str(member.id),
                                    description=f"ID: {member.id}",
                                )
                                for member in chunk
                            ]

                            user_select = Select(
                                placeholder="추가할 유저를 선택하세요",
                                options=options,
                                max_values=len(options)  # 현재 청크 내의 모든 멤버 선택 가능
                            )

                            async def user_select_callback(inner_interaction: discord.Interaction):
                                selected_users = [int(user_id) for user_id in user_select.values]
                                usernames = [
                                    inner_interaction.guild.get_member(user_id).mention
                                    for user_id in selected_users
                                ]

                                # 선택된 유저를 티켓 채널에 추가
                                for user_id in selected_users:
                                    member = inner_interaction.guild.get_member(user_id)
                                    if member:
                                        await ticket_channel.set_permissions(
                                            member, read_messages=True, send_messages=True
                                        )

                                await inner_interaction.response.edit_message(
                                    content=f"선택된 유저가 티켓에 추가되었습니다: {', '.join(usernames)}",
                                    view=None,  # 추가 완료 후 뷰 제거
                                )
                                await ticket_channel.send(
                                    f"<@{inner_interaction.user.id}>님께서 {', '.join(usernames)}님을 티켓에 추가하였습니다."
                                )

                            user_select.callback = user_select_callback

                            prev_button = Button(
                                label="이전", style=discord.ButtonStyle.secondary,
                                disabled=(chunk_index == 0)
                            )
                            next_button = Button(
                                label="다음", style=discord.ButtonStyle.secondary,
                                disabled=(chunk_index == len(chunks) - 1)
                            )

                            async def prev_button_callback(inner_interaction: discord.Interaction):
                                await inner_interaction.response.edit_message(
                                    content="유저를 추가할 멤버를 선택해주세요:",
                                    view=await create_member_selection_view(chunk_index - 1)
                                )

                            async def next_button_callback(inner_interaction: discord.Interaction):
                                await inner_interaction.response.edit_message(
                                    content="유저를 추가할 멤버를 선택해주세요:",
                                    view=await create_member_selection_view(chunk_index + 1)
                                )

                            prev_button.callback = prev_button_callback
                            next_button.callback = next_button_callback

                            view = View()
                            view.add_item(user_select)
                            view.add_item(prev_button)
                            view.add_item(next_button)

                            return view

                        # 첫 번째 청크 뷰를 생성하고 메시지를 수정
                        view = await create_member_selection_view(0)
                        await interaction.followup.send(
                            content="유저를 추가할 멤버를 선택해주세요:",
                            view=view,
                            ephemeral=True
                        )

                    elif select.values[0] == "유저 제거":
                        await interaction.followup.send(
                            content="유저 제거 기능은 현재 준비 중입니다!",
                            ephemeral=True
                        )

                select.callback = select_callback
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