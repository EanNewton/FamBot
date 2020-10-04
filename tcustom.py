#!/usr/bin/python3
#TODO add embeds
#TODO add rich support such as dates

from copy import deepcopy

import pendulum
from sqlalchemy import and_, update, insert, delete, select, MetaData, Table, Column, Integer, String

import tquote
import tword
import tsched
from tutil import is_admin, debug, guildList, fetch_value
from constants import ENGINE, TZ_ABBRS

customCommands = dict()

def get_userByID(user_id):
	return main.bot.get_user(user_id)

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
    """Grab any custom commands from the database"""
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

    if args[0] in {'!custom',}:
        if args[1] == 'help':
            return getHelp(message)
        return customCommands[message.guild.id]
	
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
        #for nested commands
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
                    return banner
                else:
                    count += 1
                    prev = deepcopy(banner)
    except:
        pass
    finally:
        return banner


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
    """Permanently remove a custom command if it exists"""
    if is_admin(message.author):
        args = message.content.split()[1:]
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


def getHelp(message):
    pass



setup()