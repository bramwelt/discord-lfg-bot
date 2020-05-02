"""LFG Bot"""
import logging
import sys
from os import getenv

import discord
from discord.ext import commands

DESCRIPTION = '''An LFG bot.'''
TOKEN = getenv("BOT_TOKEN")

bot = commands.Bot(command_prefix='!', description=DESCRIPTION)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lfg')


def role_to_slug(role: str):
    """Covert a role to a 'slugified' name for channels"""
    return role.lower().replace(' ', '-')

def game_to_role(game: str):
    """Coverts a game to a human readable role name"""
    return game.replace('-', ' ').capitalize()

def available_games(ctx):
    """List the available LFG games"""
    # exclude_roles = [bot.user.name, ctx.guild.default_role]
    guild_bot = ctx.guild.get_member(bot.user.id)
    exclude_roles = [ctx.guild.default_role]
    # Exclude the first role which is always the Guild's `@everyone`
    #  Maybe better to look this up instead of doing a [1:]
    return [role for role in guild_bot.roles if role not in exclude_roles]

@bot.event
async def on_ready():
    """On Ready output"""
    logger.info(f'Logged in as {bot.user.name}: {bot.user.id}')

@bot.group()
async def lfg(ctx):
    """Looking For Group command group
    All commands are a sub-command of this group.
    """
    logger.info(f'"{ctx.message.content}" recieved from {ctx.message.author} on {ctx.guild}')
    if ctx.invoked_subcommand is None:
        lfg_commands = [command.name for command in lfg.commands]
        await ctx.send('Missing command. Pass one of: {0}'.format(", ".join(lfg_commands)))

@commands.guild_only()
@lfg.command(name='list-games', pass_context=True)
async def list_games(ctx):
    """Lists LFG games (the bot roles) on the server"""
    # exclude_roles = [bot.user.name, ctx.guild.default_role]
    games = available_games(ctx)
    if len(games) == 0:
        await ctx.send("No LFG groups defined. Aak an admin to create one with '!lfg add-game'")
        return
    game_names = ", ".join([game.name for game in games])
    await ctx.send("Games: {}".format(game_names))

@commands.guild_only()
@lfg.command(name='add')
async def add_to_group(ctx, *, game: str):
    """Adds the user to the specific LFG group"""
    # Create a role, enroll the member in it
    guild = ctx.guild
    member = ctx.message.author

    # Check if role exists on bot, if not fail
    roles = ctx.guild.get_member(bot.user.id).roles
    game_role = None
    for role in roles:
        if game == role.name:
            game_role = role
    if game_role is None:
        await ctx.send("LFG group not found.")
        return

    # If so, add the member to the role
    logger.info(f'{member} added to role {game} on {guild}')
    await member.add_roles(game_role)
    channel_name = role_to_slug(game_role.name)
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if not channel:
        await ctx.send("Channel does not exist for {}".format(game))
        return
    await ctx.send(f"Find a group in {channel.mention}!")

@commands.guild_only()
@lfg.command(name='remove')
async def remove_from_group(ctx, *, game: str):
    """Removes the user from the LFG group"""
    member = ctx.message.author

    # Check if role exists on bot, if not fail
    roles = ctx.guild.get_member(bot.user.id).roles
    game_role = None
    for role in roles:
        if game == role.name:
            game_role = role
    if game_role is None:
        await ctx.send("{} group not found.".format(game))
        return

    # If so, remove the member from the role
    logger.info(f'{member} removed role {game} on {ctx.guild}')
    await member.remove_roles(game_role)

@commands.guild_only()
@lfg.command(name='add-game', pass_context=True)
async def add_game(ctx, *, game: str):
    """Creates a new LFG game on the server"""
    guild = ctx.guild
    channels = guild.channels

    role = await guild.create_role(name=game_to_role(game))

    # Add bot to role
    bot_member = ctx.guild.get_member(bot.user.id)
    await bot_member.add_roles(role)
    logger.info(f'{role.name} created on {guild}')

    channel = None
    for chan in channels:
        if chan.name == role_to_slug(role.name):
            channel = chan

    if not channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        channel = await guild.create_text_channel(role.name, overwrites=overwrites)

    await ctx.send("New game added: {}".format(game_to_role(game)))

@commands.guild_only()
@lfg.command(name='remove-game', pass_context=True)
async def remove_game(ctx, game: str):
    """Creates a new LFG group on the server"""
    await ctx.send("Removing game: {}".format(game))


bot.run(TOKEN)
