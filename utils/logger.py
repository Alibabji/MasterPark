import discord
from dotenv import load_dotenv
import os

load_dotenv()

GLOBAL_LOG_CHANNEL_ID = int(os.getenv('GLOBAL_LOG_CHANNEL_ID'))


def setup_logger(bot):
    @bot.event
    async def on_message_edit(before, after):
        if after.guild is None or after.author.bot:
            return

        # Get the log channel
        log_channel = bot.get_channel(GLOBAL_LOG_CHANNEL_ID)

        if log_channel is None:
            print(f"Log channel with ID {GLOBAL_LOG_CHANNEL_ID} not found.")
            return

        # Check if message content has been edited
        if before.content != after.content:
            embed = discord.Embed(
                description=f"Message edited in {after.channel.mention}",
                color=0xfc6ddd
            )
            embed.set_author(name=str(after.author), icon_url=after.author.display_avatar.url)
            embed.add_field(name="Before", value=before.content or "No content", inline=False)
            embed.add_field(name="After", value=after.content or "No content", inline=False)
            embed.add_field(name="Message Link", value=f"[Jump to message]({after.jump_url})", inline=True)
            embed.add_field(name="Channel ID", value=after.channel.id, inline=True)
            embed.add_field(name="Message ID", value=after.id, inline=True)

            await log_channel.send(embed=embed)

        # Check if attachments have been removed
        if len(before.attachments) > len(after.attachments):
            removed_attachments = [att for att in before.attachments if att not in after.attachments]

            for attachment in removed_attachments:
                embed = discord.Embed(
                    description=f"Attachment removed in {after.channel.mention} due to message edit",
                    color=discord.Color.blurple()
                )
                embed.set_author(name=str(after.author), icon_url=after.author.display_avatar.url)
                embed.add_field(name="Attachment Name", value=attachment.filename, inline=False)
                embed.add_field(name="Size", value=f"{attachment.size} bytes", inline=False)
                embed.add_field(name="Original Link", value=attachment.url, inline=False)
                embed.add_field(name="Message Link", value=f"[Jump to message]({after.jump_url})", inline=False)
                embed.add_field(name="Member ID", value=after.author.id, inline=True)
                embed.add_field(name="Channel ID", value=after.channel.id, inline=True)
                embed.add_field(name="Message ID", value=after.id, inline=True)

                await log_channel.send(embed=embed)
