#!/usr/bin/python3
#TODO add embeds
#TODO add rich support such as dates

from copy import deepcopy

import pendulum
from sqlalchemy import and_, update, insert, delete, select, MetaData, Table, Column, Integer, String

import tquote
import tword
import tsched
from tutil import is_admin, debug, guildList, fetch_value, incrementUsage, fetchFile, wrap
from constants import ENGINE, TZ_ABBRS, DIVIDER


#Nested dictionary
#{key = guild.id, value = dictionary{
#   key = command name,  value = command return String}
#}
customCommands = dict()

def setup():
    global meta, Commands
    meta = MetaData()
    Commands = Table(
        'commands', meta,
        Column('id', Integer, primary_key = True),
        Column('guild_id', Integer),
        Column('guild_name', String),
        Column('name', String),
    Column('value', String),
    )
    meta.create_all(ENGINE)
    guilds = guildList()
    for each in guilds:
        importCustomCommands(each)
    print('[+] End Custom Commands Setup')


def importCustomCommands(guild):
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
                commands[each[3]] = each[4] 
            customCommands[guild] = commands


def get_command(message):
    """
    Return a custom command to be sent to Discord.
    :param message: <Discord.message> Raw message object
    :return: <str> Banner
    """
    banner = None
    args = message.content.split()
    config = tsched.load_config(message.guild.id)

    if args[0] in {'!custom'}:
        return getHelp(message)
	
    if config:
        server_locale = config[2]
        url = config[6]
        timestamp = pendulum.now(tz=server_locale).to_datetime_string()
    else:
        url = ' '
        timestamp = pendulum.now(tz='America/New_York').to_datetime_string()

    try:
        guildCommands = customCommands[message.guild.id]
        banner = guildCommands[args[0]]
        #for nested commands, not the most efficient solution but it works
        prev = deepcopy(banner)
        count = 0
        while True:
            if len(banner) + len(prev) > 1990 or count > 50:
                return banner
            else:
                for key in guildCommands:
                    banner = banner.replace('<{}>'.format(key), guildCommands[key])        
                #TODO user mentions for <QUOTE>
                banner = banner.replace('<URL>', url)
                banner = banner.replace('<NOW>', '{} in {}'.format(timestamp, server_locale))
                banner = banner.replace('<TIME>', '{} in {}'.format(timestamp, server_locale))
                banner = banner.replace('<LOCALE>', server_locale)
                banner = banner.replace('<LOCATION>', server_locale)
                banner = banner.replace('<AUTHOR>', message.author.name)
                banner = banner.replace('<GUILD>', message.guild.name)
                banner = banner.replace('<SCHED>', tsched.getSchedule(message))
                banner = banner.replace('<QUOTE>', tquote.getQuote(message.guild.id, tquote.Quotes))
                banner = banner.replace('<LORE>', tquote.getQuote(message.guild.id, tquote.Lore))
                if banner == prev:
                    return wrap(banner, 1990)
                else:
                    count += 1
                    prev = deepcopy(banner)
        if banner:
            incrementUsage(message.guild, 'custom')
    except:
        pass
    finally:
        if banner: 
            return wrap(banner, 1990)


def insert_command(message):
    """
    Add a new custom command to the database.
    :param message: <Discord.message> Raw message object
    :return: <str> Banner notifying if new command has been created or exisisting has been updated.
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
                ins = Commands.update().where(and_(
                    Commands.c.guild_name == message.guild.name,
                    Commands.c.name == args[0])).values(
                        value = ' '.join(args[1:]),
                    )
                conn.execute(ins)
                importCustomCommands(message.guild.id)
                return 'Updated `{}` to return: "{}".'.format(args[0], ' '.join(args[1:]))
            else:
                ins = Commands.insert().values(
                    id = message.id,
                    guild_id = message.guild.id,
                    guild_name = message.guild.name,
                    name = args[0],
                    value = ' '.join(args[1:]),
                )
                conn.execute(ins)
                importCustomCommands(message.guild.id)
                return '`{}` will now display:\n {}.'.format(args[0], ' '.join(args[1:]))


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
                importCustomCommands(message.guild.id)
                return 'Deleted {}'.format(args[0])
            else:
                return 'Command `{}` does not exist.'.format(args[0])


def getHelp(message):
    """
    Get the command help file from ./docs/help
    :param message: <Discord.message object>
    :return: <String> Containing help for the user's available options or list of locations
    """
    incrementUsage(message.guild, 'help')
    banner = None
    try:
        guildCommands = customCommands[message.guild.id]
        banner = fetchFile('help', 'custom')
        banner = '{}\n{}Custom commands available in this server are:\n'.format(banner, DIVIDER)
        for name, value in guildCommands.items():
            banner = '{}`{}`: {}\n'.format(banner, name, value)
    except:
        pass
    finally:
        return wrap(banner, 1990)


setup()