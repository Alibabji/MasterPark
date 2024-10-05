import math
import aiohttp
from discord import Activity, ActivityType, Embed, File

unit = [
    {"value": 1, "symbol": ""},
    {"value": 1e3, "symbol": "k"},
    {"value": 1e6, "symbol": "M"},
    {"value": 1e9, "symbol": "G"},
    {"value": 1e12, "symbol": "T"},
    {"value": 1e15, "symbol": "P"},
    {"value": 1e18, "symbol": "E"},
]

class Util:
    @staticmethod
    def bytes_to_size(bytes: int):
        sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
        if bytes <= 1:
            return f"{bytes} Byte"
        i = int(math.floor(math.log(bytes, 1024)))
        s = f" ({Util.comma(bytes)} Bytes)" if i > 0 else ''
        return f"{Util.comma(round(bytes / (1024 ** i), 2))} {sizes[i]}{s}"

    @staticmethod
    async def send_file(ctx, attachment, guild, embed):
        if guild and attachment.size > Util.get_file_size_limit(guild):
            await ctx.send(content="(Server attachment limit exceeded)", embed=embed)
        else:
            try:
                await ctx.send(file=File(attachment), embed=embed)
            except:
                await ctx.send(content="(Server attachment limit exceeded)", embed=embed)

    @staticmethod
    def comma(x: int):
        return f"{x:,}"