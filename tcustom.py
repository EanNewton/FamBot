#!/usr/bin/python3
#TODO add embeds
#TODO add rich support such as dates

from sqlalchemy import and_, update, insert, delete, select, MetaData, Table, Column, Integer, String

from tutil import is_admin, debug, guildList, fetch_value
from constants import ENGINE

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
    """Return a custom command to be sent to Discord"""
    banner = None
    try:
        guildCommands = customCommands[message.guild.id]
        banner = guildCommands[message.content]
    except:
        pass
    finally:
        return banner


def insert_command(message):
    """Add a new custom command to the database"""
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

setup()