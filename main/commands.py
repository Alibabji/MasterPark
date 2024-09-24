from storage import save_user, get_user
from riot_api import check_summoner_exists


def setup_commands(bot):
    # Command to connect League of Legends IGN
    @bot.command()
    async def connectlol(ctx, nickname):
        discord_id = ctx.author.id

        # Check if the summoner exists using Riot API
        if check_summoner_exists(nickname):
            # Check if the user already exists in the database
            existing_nickname = get_user(discord_id)

            if existing_nickname:
                await ctx.send(
                    f"Your League of Legends nickname is already saved as {existing_nickname}. If you want to update it, save a new one!")
            else:
                # Save the new nickname to the file
                save_user(discord_id, nickname)
                await ctx.send(f"Your League of Legends nickname, {nickname}, has been saved.")
        else:
            await ctx.send(f"Error: The League of Legends nickname '{nickname}' does not exist.")

    # Command to retrieve user's League of Legends IGN
    @bot.command()
    async def mylol(ctx):
        discord_id = ctx.author.id

        # Retrieve the user's nickname
        nickname = get_user(discord_id)

        if nickname:
            await ctx.send(f"Your connected League of Legends nickname is {nickname}.")
        else:
            await ctx.send("You haven't connected your League of Legends nickname yet.")
