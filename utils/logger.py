import discord
from dotenv import load_dotenv
import os
from .utils import Util

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
                embed.add_field(name="Size", value=f"{Util.bytes_to_size(attachment.size)}", inline=False)
                embed.add_field(name="Original Link", value=attachment.url, inline=False)
                embed.add_field(name="Message Link", value=f"[Jump to message]({after.jump_url})", inline=False)
                embed.add_field(name="Member ID", value=after.author.id, inline=True)
                embed.add_field(name="Channel ID", value=after.channel.id, inline=True)
                embed.add_field(name="Message ID", value=after.id, inline=True)

                await log_channel.send(embed=embed)

    @bot.event
    async def on_message_delete(msg: discord.Message):
        if not msg.guild:
            return
        if msg.author.bot:
            return

        log_channel = bot.get_channel(GLOBAL_LOG_CHANNEL_ID)
        if log_channel is None:
            print(f"Log channel with ID {GLOBAL_LOG_CHANNEL_ID} not found.")
            return

        for attachment in msg.attachments:
            embed = discord.Embed(
                description=f"An attachment was deleted in {msg.channel.mention}",
                color=0xD36E70
            )
            embed.set_author(name=msg.author, icon_url=msg.author.display_avatar.url)
            embed.add_field(name="Name", value=attachment.filename or 'file')
            embed.add_field(name="Size", value=Util.bytes_to_size(attachment.size))
            embed.add_field(name="Original Link", value=attachment.url)
            embed.set_footer(text=f"Member: {msg.author.id} \nChannel: {msg.channel.id} \nMessage: {msg.id}")
            await log_channel.send(embed=embed)

            # Handle message content
        if len(msg.content) > 0:
            embed = discord.Embed(
                description=f"A message was deleted in {msg.channel.mention}",
                color=0xD36E70
            )
            embed.set_author(name=msg.author, icon_url=msg.author.display_avatar.url)
            embed.add_field(name="Content", value=msg.content)
            embed.set_footer(text=f"Member: {msg.author.id} \nChannel: {msg.channel.id} \nMessage: {msg.id}")
            await log_channel.send(embed=embed)

            # Handle stickers
        for sticker in msg.stickers:
            embed = discord.Embed(
                description=f"A sticker was deleted in {msg.channel.mention}",
                color=0xD36E70
            )
            embed.set_author(name=msg.author, icon_url=msg.author.display_avatar.url)
            embed.set_thumbnail(url=sticker.url)
            embed.add_field(name="Name", value=sticker.name)
            embed.add_field(name="Link", value=sticker.url)
            embed.add_field(name="Format", value=sticker.format)
            embed.set_footer(
                text=f"Member: {msg.author.id} \nChannel: {msg.channel.id} \nMessage: {msg.id} \nSticker: {sticker.id}")

            # Send the embed to the log channel
            await log_channel.send(embed=embed)