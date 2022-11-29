#!/usr/bin/python3

# TODO Add restricted channels
# TODO Add !push to notify guild owners of updates
# TODO Create a GUI config app
# TODO Scheduled commands
# TODO Add option to delete command request message
# TODO Server counts

import functools
import json
import time

import aiofiles
import aiohttp
import discord
from sqlalchemy import select, MetaData, Table, Column, Integer, String

from constants import DEFAULT_DIR, jsonFormatter, ENGINE, VERBOSE

modRoles = dict()


def setup() -> None:
    global meta, Config, Stats
    meta = MetaData()
    Config = Table(
        'config', meta,
        Column('id', Integer, primary_key=True),
        Column('guild_name', String),
        Column('locale', String),
        Column('schedule', String),
        Column('quote_format', String),
        Column('lore_format', String),
        Column('url', String),
        Column('qAdd_format', String),
        Column('filtered', String),
        Column('mod_roles', String),
        Column('anonymous', Integer),
        #    Column('timer_channel', Integer),
    )
    Stats = Table(
        'usageCounts', meta,
        Column('id', Integer, primary_key=True),
        Column('guild_name', String),
        Column('raw_messages', Integer),
        Column('quote', Integer),
        Column('lore', Integer),
        Column('wolf', Integer),
        Column('wotd', Integer),
        Column('dict', Integer),
        Column('trans', Integer),
        Column('google', Integer),
        Column('config', Integer),
        Column('sched', Integer),
        Column('filter', Integer),
        Column('doip', Integer),
        Column('gif', Integer),
        Column('stats', Integer),
        Column('eight', Integer),
        Column('help', Integer),
        Column('custom', Integer),
    )
    meta.create_all(ENGINE)
    update_mod_roles()
    if VERBOSE >= 0:
        print('[+] End Util Setup')


#############################
# General Utility Functions #
#############################
def debug(func):
    """Print the function signature and return value"""
    if VERBOSE >= 1:
        @functools.wraps(func)
        def wrapper_debug(*args, **kwargs):
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)

            print(f"Calling {func.__name__}({signature})\n")
            value = func(*args, **kwargs)
            print(f"{func.__name__!r} returned {value!r}\n")

            return value

        return wrapper_debug
    else:
        return func


def sleep(timeout, retry=3):
    """
    Sleep decorator, usage: @sleep(3)
    :param timeout:
    :param retry:
    :return:
    """

    def the_real_decorator(function):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    value = function(*args, **kwargs)
                    if value is None:
                        return
                except Exception as e:
                    if VERBOSE >= 1:
                        print(e)
                        print(f'Sleeping for {timeout} seconds')
                    time.sleep(timeout)
                    retries += 1

        return wrapper

    return the_real_decorator


def fetch_file(directory: str, filename: str):
    """
    Safely read in a dynamically designated local file
    :param directory:
    :param filename:
    :return:
    """
    with open('{}/docs/{}/{}.txt'.format(DEFAULT_DIR, directory, filename), 'r') as f:
        return f.read()


@debug
async def is_admin(author: discord.User, message: discord.Message) -> bool:
    """
	Check if a discord user has been given bot admin permissions
    :param message:
	:param author: <Discord.message.author object>
	:return: <bool>
	"""
    try:
        print(type(author))
        print(author)
    except Exception as e:
        print(e)
    if type(author) is discord.User and not author.bot:
        if author.id == 184474309891194880 or author.id == message.guild.owner_id:
            return True
        else:
            await author.send(content='Role based permissions are not currently supported by DiscordPy in private \
channels. Please try again in a different channel, or the guild owner can issue the command here.')
            return False
    else:
        try:
            if author.guild.owner_id == author.id or author.id == 184474309891194880:
                return True
        except Exception as e:
            if VERBOSE >= 2:
                print("Exception in is_admin: {}".format(e))
            else:
                pass
        try:
            for role in author.roles:
                if str(role).lower() in modRoles[author.guild.id]:
                    return True
        except Exception as e:
            if VERBOSE >= 2:
                print("Exception in is_admin: {}".format(e))
            else:
                pass
        return False


@debug
async def is_admin_test(author: discord.User, message: discord.Message) -> bool:
    """
	Check if a discord user has been given bot admin permissions
    :param message:
	:param author: <Discord.message.author object>
	:return: <bool>
	"""

    if type(author) is discord.User and not author.bot:
        if author.id == 184474309891194880 or author.id == message.guild.owner_id:
            return True
        else:
            await author.send(content='Role based permissions are not currently supported by DiscordPy in private \
channels. Please try again in a different channel, or the guild owner can issue the command here.')
            return False
    else:
        try:
            if author.guild.owner_id == author.id or author.id == 184474309891194880:
                return True
        except Exception as e:
            if VERBOSE >= 2:
                print("Exception in is_admin: {}".format(e))
            else:
                pass
        try:
            for role in author.roles:
                if str(role).lower() in modRoles[author.guild.id]:
                    return True
        except Exception as e:
            if VERBOSE >= 2:
                print("Exception in is_admin: {}".format(e))
            else:
                pass
        return False


def wrap(s: str, w: int) -> list:
    """
    Break a long string s into a list of strings of length w
    :param s:
    :param w:
    :return:
    """
    return [s[i:i + w] for i in range(0, len(s), w)]


def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


def flatten_sublist(l: list):
    """
    Convert a list of lists l into a flat list
    :param l:
    :return:
    """
    return [item for sublist in l for item in sublist]


############################
# Config Utility Functions #
############################
def increment_usage(guild: discord.guild, command: str) -> int:
    """Keeps track of how many times various commands have been used"""
    with ENGINE.connect() as conn:
        select_st = select([Stats]).where(Stats.c.id == guild.id)
        result = conn.execute(select_st).fetchone()

        if result:
            columns = []
            for each in Stats.c:
                columns.append(each.name)
            dict_ = dict(zip(columns, result))
            dict_[command] = int(dict_[command]) + 1

            ins = Stats.update().where(Stats.c.id == guild.id).values(
                raw_messages=dict_['raw_messages'],
                quote=dict_['quote'],
                lore=dict_['lore'],
                wolf=dict_['wolf'],
                wotd=dict_['wotd'],
                dict=dict_['dict'],
                trans=dict_['trans'],
                google=dict_['google'],
                config=dict_['config'],
                sched=dict_['sched'],
                filter=dict_['filter'],
                doip=dict_['doip'],
                gif=dict_['gif'],
                stats=dict_['stats'],
                eight=dict_['eight'],
                help=dict_['help'],
                custom=dict_['custom'],
            )
            conn.execute(ins)
            # TODO why are we returning 1?
            return 1

        else:
            if VERBOSE >= 2:
                print('[+] Creating usage counter for {}'.format(guild.name))
            ins = Stats.insert().values(
                id=guild.id,
                guild_name=guild.name,
                raw_messages=0,
                quote=0,
                lore=0,
                wolf=0,
                wotd=0,
                dict=0,
                trans=0,
                google=0,
                config=0,
                sched=0,
                filter=0,
                doip=0,
                gif=0,
                stats=0,
                eight=0,
                help=0,
                custom=0,
            )
            conn.execute(ins)
            return increment_usage(guild, command)


@debug
async def config_helper(message: discord.Message):
    """
	Create or reset the server config entry
	:param message: <Discord.message object>
	:return: <String> Describing file location
	"""

    increment_usage(message.guild, 'config')

    if await is_admin(message.author, message):
        args = message.content.split()
        if len(args) > 1 and args[1] == 'reset':
            return config_reset(message.guild)
        else:
            return config_create(message.guild)


def update_mod_roles() -> None:
    """
	Sync in-memory mod roles with database values for all guilds
	:return: <None>
	"""

    for guild in guild_list():
        roles = fetch_value(guild, 9, ';')
        if roles:
            modRoles[guild] = [str(role).lower() for role in roles]
            if VERBOSE >= 1:
                print('[+] Updated mod roles')


@debug
def config_create(guild: discord.guild) -> str:
    """
	Get the config file for the server and give to the user
	:param guild: <Discord.guild object>
	:return: <String> Describing file location
	"""

    with ENGINE.connect() as conn:
        select_st = select([Config]).where(Config.c.id == guild.id)
        result = conn.execute(select_st).fetchone()

        if result:
            if VERBOSE >= 2:
                print('[+] Found guild config for {}'.format(guild.name))
            # Create an in-memory version of the config
            columns = []
            for each in Config.c:
                columns.append(each.name)
            dict_ = dict(zip(columns, result))

            # For pretty printing, make the user's life easier
            for each in jsonFormatter[0]:
                dict_['schedule'] = dict_['schedule'].replace(each[0], each[1])
            for each in jsonFormatter[1]:
                dict_[each[1]] = dict_.pop(each[0])

            with open('{}/docs/config/{}.json'.format(DEFAULT_DIR, guild.id), 'w') as f:
                json.dump(dict_, f, indent=4)
                f.write('\n\n{}'.format(fetch_file('help', 'config')))
            return '{}/docs/config/{}.json'.format(DEFAULT_DIR, guild.id)

        else:
            # Guild has no config entry, create one and try again
            config_create_default(guild)
            return config_create(guild)


def config_create_default(guild: discord.guild) -> None:
    """
	Create a new default entry for the given guild
	:param guild: <Discord.guild object>
	:return: <None>
	"""

    if VERBOSE >= 1:
        print('[+] Creating new guild config for {}'.format(guild.name))

    with ENGINE.connect() as conn:
        ins = Config.insert().values(
            id=guild.id,
            guild_name=guild.name,
            locale='Asia/Tokyo',
            schedule='0=10,17:15;1=10,12;2=16,10:15;3=2:44;4=10;5=16:30;',
            quote_format='**{}**\n{}\n ---{} on {}',
            lore_format='**{}**\n{}\n---Scribed by the Lore Master {}, on the blessed day of {}',
            url='Come hang with us at: <https://www.twitch.tv/>',
            qAdd_format='Added:\n \"{0}\"\n by {1} on {2}',
            filtered='none',
            mod_roles='mod;admin;discord mod;',
            anonymous=1,
            #   timer_channel=0,
        )
        conn.execute(ins)


def config_load(guild: int) -> None:
    """
	Load the JSON file supplied by user into the database
	:param guild: <Int> Discord guild ID
	:return: <None>
	"""

    # Undo the pretty printing
    with open('{}/docs/config/{}.json'.format(DEFAULT_DIR, guild), 'r') as f:
        dict_ = json.loads(f.read().split('```', maxsplit=1)[0])
    for each in jsonFormatter[1]:
        dict_[each[0]] = dict_.pop(each[1])
    for each in jsonFormatter[0]:
        dict_['schedule'] = dict_['schedule'].replace(each[1], each[0])

    with ENGINE.connect() as conn:
        ins = Config.update().where(Config.c.id == guild).values(
            locale=dict_['locale'],
            schedule=dict_['schedule'],
            quote_format=dict_['quote_format'],
            lore_format=dict_['lore_format'],
            url=dict_['url'],
            qAdd_format=dict_['qAdd_format'],
            filtered=dict_['filtered'],
            mod_roles=dict_['mod_roles'],
            anonymous=dict_['anonymous'],
            #   timer_channel=dict_['timer_channel'],
        )
        conn.execute(ins)
    # TODO ensure to lower
    modRoles[guild] = fetch_value(guild, 9, ';')
    if VERBOSE >= 1:
        print('[+] Loaded new config for {}'.format(guild.name))


def config_reset(guild: int) -> str:
    """
	Return the config to default values
	:param guild: <Discord.guild object>
	:return: <None>
	"""
    with ENGINE.connect() as conn:
        ins = Config.delete().where(Config.c.id == guild.id)
        conn.execute(ins)
    if VERBOSE >= 1:
        print('[+] Reset config for: {}'.format(guild.name))
    return config_create(guild)


async def config_fetch_embed(message: discord.Message) -> None:
    """
	User has uploaded a new config file, grab it from the Discord servers
	:param message: <Discord.message object>
	:return: <None>
	"""
    filePath = '{}/docs/config/{}.json'.format(DEFAULT_DIR, message.guild.id)

    async with aiohttp.ClientSession() as session:
        async with session.get(str(message.attachments[0].url)) as resp:
            if resp.status == 200:
                f = await aiofiles.open(filePath, mode='wb')
                await f.write(await resp.read())
                await f.close()
                if VERBOSE >= 1:
                    print('[+] Saved: {}'.format(filePath))

    config_load(message.guild.id)


def fetch_value(guild: int, val: str, delim=None) -> list:
    """
	Get a specific cell from the guilds config table
	:param guild: <Int> Discord guild ID
	:param val: <String> Column name within Config Table
	:param delim: (Optional) <String> Delimeter for splitting values within the cell
	:return: <List> Values from within the specified cell
	"""

    with ENGINE.connect() as conn:
        select_st = select([Config]).where(Config.c.id == guild)
        res = conn.execute(select_st)
        result = res.fetchone()

    if result and result[val]:
        if type(result[val]) is str:
            result = result[val].split(delim)
            result[:] = (val for val in result if val not in {'', ' ', '\n', None})
        else:
            result = result[val]
        return result


def fetch_config(guild: int) -> list:
    """
	Internal function to get Guild configuration data for schedule formatting and default locale
	:param guild: <Int> Discord guild ID
	:return: <List> SQLAlchemy row result from database
	"""

    with ENGINE.connect() as conn:
        select_st = select([Config]).where(Config.c.id == guild)
        res = conn.execute(select_st)
        result = res.fetchone()
    if result:
        return result
    return None


def guild_list() -> list:
    """
	Get a list of all guilds ids
	:return: <List> IDs for all guilds the bot is active in
	"""

    with ENGINE.connect() as conn:
        select_st = select([Config])
        res = conn.execute(select_st)
        result = res.fetchall()

    return [each[0] for each in result]


# TODO Implement this
# def update_self():
#     elif message.content.startswith('!update'):
#         authorizedUsers = config['discord']['AuthorizedUsers'].split(',')
#         userID = message.author.id
#         if str(userID) in authorizedUsers:
#             subprocess.run(["git", "fetch", "origin"])
#             out = subprocess.check_output(["git", "rev-list", "--count", "origin/master...master"])
#             commitsBehind = int(str(out.decode("utf-8")).rstrip())
#             if commitsBehind > 0 and videoPlaying == False:
#                 await channel.send('You are ' + str(out.decode("utf-8")).rstrip() + ' commits behind')
#                 await channel.send('Updating')
#                 videoPlaying = True
#                 subprocess.run(["git", "reset", "--hard", "origin/master"])
#                 subprocess.run(["systemctl", "restart", "videobot"])
#             elif commitsBehind > 0 and videoPlaying == True:
#                 await channel.send('You are ' + str(out.decode("utf-8")).rstrip() + ' commits behind')
#                 await channel.send('Run this command when a video isn\'t streaming to update')
#             else:
#                 await channel.send('Videobot is up to date')
#         else:
#             await channel.send('Unauthorized User')


setup()
