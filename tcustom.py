#!/usr/bin/python3
# TODO add embeds
# TODO add rich support such as dates

from copy import deepcopy

import pendulum
from discord import Embed
from sqlalchemy import and_, select, MetaData, Table, Column, Integer, String

import tquote
import tsched
from tutil import is_admin,  guild_list, fetch_value, increment_usage, fetch_file, debug
from constants import ENGINE, VERBOSE, extSet

custom_commands = dict()


def setup():
    global meta, Commands
    meta = MetaData()
    Commands = Table(
        'commands', meta,
        Column('id', Integer, primary_key=True),
        Column('guild_id', Integer),
        Column('guild_name', String),
        Column('name', String),
        Column('embed', String),
        Column('value', String),
    )
    meta.create_all(ENGINE)
    guilds = guild_list()
    for each in guilds:
        import_custom_commands(each)
    if VERBOSE >= 0:
        print('[+] End Custom Commands Setup')


def import_custom_commands(guild):
    """
    Internal function to grab any custom commands from the database
    :param guild: <Int> Discord guild ID
    :return: <None>
    """
    name = ' '.join(fetch_value(guild, 1))

    with ENGINE.connect() as conn:
        select_st = select([Commands]).where(
            Commands.c.guild_name == name
        )
        result = conn.execute(select_st).fetchall()

        if result:
            commands = dict()
            for each in result:
                each = list(each)
                commands[each[3]] = each[5]
            custom_commands[guild] = commands

@debug
def get_command(message):
    """
    Return a custom command to be sent to Discord.
    :param message: <Discord.message> Raw message object
    :return: <str> Banner
    """
    embed_image = None
    links = ''
    custom = '.'
    args = message.content.split()
    config = tsched.load_config(message.guild.id)
    quotes = False

    if VERBOSE >= 2:
        print("Config: ")
        print(config)

    try:
        if args[0] == '$custom' or args[0:2] == ['$help', 'custom']:
            if VERBOSE >= 1:
                print('[-] custom - help by {} in {} - {}'.format(
                    message.author.name, message.channel.name, message.guild.name))
            return get_help(message)
    except Exception as e:
        if VERBOSE >= 2:
            print("Exception: ")
            print(e)

    if config:
        server_locale = config[2]
        url = config[6]
        timestamp = pendulum.now(tz=server_locale).to_datetime_string()
    else:
        url = ' '
        timestamp = pendulum.now(tz='America/New_York').to_datetime_string()
        server_locale = 'America/New_York'

    try:
        # all custom commands for the guild
        guild_commands = custom_commands[message.guild.id]
        if VERBOSE >= 2:
            print("Guild Commands: ")
            print(guild_commands)
        # the value to be returned to the user, in raw formatting
        custom = guild_commands[args[0]]
        if VERBOSE >= 2:
            print("Custom: ")
            print(custom)

        # Check for image links or general links
        if VERBOSE >= 2:
            print("Checking for links...")
        for each in custom.split():
            if each.find('http') != -1:
                if each.split('.')[-1] in extSet['image']:
                    embed_image = each
                else:
                    links = '{}\n{}'.format(links, each)
        # Setting up for nested loops
        prev = deepcopy(custom)
        count = 0

        # for nested commands, not the most efficient solution but it works
        # if you can improve it please issue a code merge request
        while True:
            if VERBOSE >= 2:
                print("Formatting command, loop {}...".format(count))
            # Discord's character limit is 2000
            # count is chosen arbitrarily, move up or down for recursion limit
            if len(custom) + len(prev) > 1999 or count > 50:
                break
            else:
                for key in guild_commands:
                    custom = custom.replace('<{}>'.format(key), guild_commands[key])
                    # TODO user mentions for <QUOTE>
                custom = custom.replace('\\n', '\n')
                custom = custom.replace('\\r', '<\n>')
                custom = custom.replace('<URL>', url)
                custom = custom.replace('<NOW>', '{} in {}'.format(timestamp, server_locale))
                custom = custom.replace('<TIME>', '{} in {}'.format(timestamp, server_locale))
                custom = custom.replace('<LOCALE>', server_locale)
                custom = custom.replace('<LOCATION>', server_locale)
                custom = custom.replace('<AUTHOR>', message.author.name)
                custom = custom.replace('<GUILD>', message.guild.name)
                while '<SCHED>' in custom:
                    custom = custom.replace('<SCHED>', tsched.get_schedule(message, True))
                #if '<QUOTE>' in custom:
                #    custom = custom.replace('<QUOTE>', tquote.get_quote(message, tquote.Quotes, raw=True))
                #    quotes = True
                custom = custom.replace('<LORE>', tquote.get_quote(message, tquote.Lore, raw=True))
                if custom == prev:
                    break
                else:
                    count += 1
                    prev = deepcopy(custom)

    except Exception as e:
        if VERBOSE >= 2:
            print('[!] Exception in tcustom {}'.format(e))
            pass
    finally:
        # Cleanup from quote with user
        if quotes:
            custom = custom.replace('>', '')
        if custom == '.':
            return None
        else:
            increment_usage(message.guild, 'custom')
            if VERBOSE >= 1:
                print('[-] custom - {} by {} in {} - {}'.format(args[0], message.author.name, message.channel.name,
                                                                message.guild.name))
            banner = Embed(title=args[0], description=custom)
            if embed_image:
                banner.set_image(url=embed_image)

            if links == '':
                links = None
            return links, banner


def insert_command(message):
    """
	Add a new custom command to the database.
	:param message: <Discord.message> Raw message object
	:return: <str> Banner notifying if new command has been created or exisisting has been updated.
	"""
    # if is_admin(message.author):
    args = message.content.split()
    links = str(message.attachments[0].url) if message.attachments else ''

    for each in args:
        if each.find('http') != -1:
            if each.split('.')[-1] in extSet['image']:
                links = '{}\n{}'.format(links, each)

    with ENGINE.connect() as conn:
        select_st = select([Commands]).where(and_(
            Commands.c.guild_id == message.guild.id,
            Commands.c.name == args[0]
        ))
        result = conn.execute(select_st).fetchone()

        if result:
            ins = Commands.update().where(and_(
                Commands.c.guild_name == message.guild.name,
                Commands.c.name == args[0])).values(
                value='{} {}'.format(' '.join(args[1:]), links),
                links=links,
            )
            conn.execute(ins)
            import_custom_commands(message.guild.id)
            banner = Embed(title='Updated `{}`'.format(args[0], description=' '.join(args[1:])))
            if VERBOSE >= 1:
                print('[+] Updated {}'.format((args[0])))
            return banner
        else:
            ins = Commands.insert().values(
                id=message.id,
                guild_id=message.guild.id,
                guild_name=message.guild.name,
                name=args[0],
                value='{} {}'.format(' '.join(args[1:]), links),
                embed=links,
            )
            conn.execute(ins)
            import_custom_commands(message.guild.id)
            banner = Embed(title='Added custom command `{}`'.format(args[0]), description=' '.join(args[1:]))
            if VERBOSE >= 1:
                print('[+] Updated {}'.format((args[0])))
            return banner


def delete_command(message):
    """
    Permanently remove a custom command if it exists
    :param message: <Discord.message object>
    :return: <String> Notifying command has been removed 
    """
    if is_admin(message.author):
        args = message.content.split()
        with ENGINE.connect() as conn:
            select_st = select([Commands]).where(and_(
                Commands.c.guild_id == message.guild.id,
                Commands.c.name == args[0]
            ))
            result = conn.execute(select_st).fetchone()
            if result:
                del_st = Commands.delete().where(and_(
                    Commands.c.guild_id == message.guild.id,
                    Commands.c.name == args[0]
                ))
                conn.execute(del_st)
                import_custom_commands(message.guild.id)
                return 'Deleted {}'.format(args[0])
            else:
                return 'Command `{}` does not exist.'.format(args[0])


def get_help(message):
    """
    Get the command help file from ./docs/help
    :param message: <Discord.message object>
    :return: <String> Containing help for the user's available options or list of locations
    """
    increment_usage(message.guild, 'help')
    custom = ''
    try:
        guild_commands = custom_commands[message.guild.id]
        banner = Embed(title='Custom Command Help', description=fetch_file('help', 'custom'))
        for name, value in guild_commands.items():
            custom = '{}`{}`: {}\n'.format(custom, name, value)
        available = Embed(title='Custom commands available in this server are:', description=custom)
        # banner.add_field(name='Custom commands available in this server are:', value=custom)
        return None, [banner, available]
    except Exception as e:
        if VERBOSE >= 0:
            print('[!] Exception in get help custom {}'.format(e))
        pass


setup()
