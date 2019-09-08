import os
import discord
from datetime import datetime

from discord.ext.commands import Bot
from mojang_api import get_uuid, is_valid_uuid, get_username_history

import hive_interface as hive
from content_functions import BlockPartyStats


BOT_PREFIX = '/'
TOKEN = os.environ['discordToken']

player_head = 'https://visage.surgeplay.com/head/96/{}'.format
client = Bot(command_prefix=BOT_PREFIX, case_insensitive=True)


@client.event
async def on_ready():
    print('Logged in as {}: {}'.format(client.user.name, client.user.id))
    await client.change_presence(activity=discord.Game(name='The Hive'))


def resolve_username(username):
    """Resolves a username to a uuid if valid

    Args:
        username (str or None): [description]

    Returns:
        bool: whether the username was valid
        str: the resolved uuid or error message
    """
    if not username:
        return False, 'Please provide a username.'

    if not is_valid_uuid(username):
        try:
            uuid = get_uuid(username).id
        except AttributeError:
            return False, 'Username or UUID was not found.'

    return True, uuid


@client.command(name='stats')
async def get_stats(ctx, uuid=None, game='BP'):
    valid, resolved = resolve_username(uuid)

    if not valid:
        await ctx.send(resolved)

    uuid = resolved
    info = hive.player_data(uuid)
    stats = hive.player_data(uuid, game)

    embed = discord.Embed(
        title='**{}** - {}'.format(info['username'],
                                   info['modernRank']['human']),
        description='{} {}'.format(info['status']['description'],
                                   info['status']['game']),
        color=0x00ff00 if info['lastLogout'] < info['lastLogin'] else 0x222222)

    embed.set_thumbnail(url=player_head(uuid))

    if game == 'BP':
        embed.add_field(name='BlockParty Stats', value=BlockPartyStats(stats))

    await ctx.send(embed=embed)


@client.command(name='names')
async def get_names(ctx, uuid=None, count: int = None):
    if count and count <= 0:
        await ctx.send('Please input a number larger than 0.')

    valid, resolved = resolve_username(uuid)

    if not valid:
        await ctx.send(resolved)

    uuid = resolved
    response = get_username_history(uuid)
    count = len(response) if count is None else count

    names = [entry.name for entry in response[::-1]]
    # Java timestamps are returned which are in millisecs, so we divide by 1000
    times = [datetime.fromtimestamp(entry.changedToAt / 1000).strftime('%d %b, %Y %H:%M')
             for entry in response[:0:-1]]
    times.append('(Original Name)')

    embed = discord.Embed(
        title='**{}\'s Name History**'.format(names[0]),
        color=0xffa500
    )

    embed.set_thumbnail(url=player_head(uuid))
    embed.add_field(name='**Names**',
                    value='\n'.join(['**{}** - {}'.format(name, time)
                                     for name, time in zip(names[:count],
                                                           times[:count])]))

    await ctx.send(embed=embed)


client.run(TOKEN)
