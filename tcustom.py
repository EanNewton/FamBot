#!/usr/bin/python3
#TODO add embeds
#TODO add rich support such as dates

from copy import deepcopy

import pendulum
from discord import Embed
from sqlalchemy import and_, update, insert, delete, select, MetaData, Table, Column, Integer, String

import tquote
import tword
import tsched
from tutil import is_admin, debug, guildList, fetch_value, incrementUsage, fetchFile, wrap
from constants import ENGINE, TZ_ABBRS, DIVIDER, extSet


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
        Column('embed', String),
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
                commands[each[3]] = each[5] 
            customCommands[guild] = commands


def get_command(message):
    """
    Return a custom command to be sent to Discord.
    :param message: <Discord.message> Raw message object
    :return: <str> Banner
    """
    custom = None
    embed_image = None
    links = ''
    custom = '.'
    args = message.content.split()
    config = tsched.load_config(message.guild.id)

    if args[0] in {'!custom'}:
        print('[-] custom - help by {} in {} - {}'.format(message.author.name, message.channel.name, message.guild.name))
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
        custom = guildCommands[args[0]]
        for each in custom.split():
            if each.find('http') != -1:
                if each.split('.')[-1] in extSet['image']:
                    embed_image = each
                else:
                    links = '{}\n{}'.format(links, each)
        prev = deepcopy(custom)
        count = 0

        #for nested commands, not the most efficient solution but it works
        while True:
            if len(custom) + len(prev) > 1990 or count > 50:
                break
            else:
                for key in guildCommands:
                    custom = custom.replace('<{}>'.format(key), guildCommands[key])        
                #TODO user mentions for <QUOTE>
                custom = custom.replace('<URL>', url)
                custom = custom.replace('<NOW>', '{} in {}'.format(timestamp, server_locale))
                custom = custom.replace('<TIME>', '{} in {}'.format(timestamp, server_locale))
                custom = custom.replace('<LOCALE>', server_locale)
                custom = custom.replace('<LOCATION>', server_locale)
                custom = custom.replace('<AUTHOR>', message.author.name)
                custom = custom.replace('<GUILD>', message.guild.name)
                custom = custom.replace('<SCHED>', tsched.getScheduleRaw(message))
                custom = custom.replace('<QUOTE>', tquote.getQuoteRaw(message.guild.id, tquote.Quotes))
                custom = custom.replace('<LORE>', tquote.getQuoteRaw(message.guild.id, tquote.Lore))
                if custom == prev:
                    break
                else:
                    count += 1
                    prev = deepcopy(custom)
    except:
        pass
    finally:
        if custom == '.':
            return None
        else:
            incrementUsage(message.guild, 'custom')
            print('[-] custom - {} by {} in {} - {}'.format(args[0], message.author.name, message.channel.name, message.guild.name))
            banner = Embed(title=args[0], description=custom)
            if embed_image:
                banner.set_image(url=embed_image)

            if links == '':
                links = None
            return links, banner

@debug
def insert_command(message):
	"""
	Add a new custom command to the database.
	:param message: <Discord.message> Raw message object
	:return: <str> Banner notifying if new command has been created or exisisting has been updated.
	"""
	#if is_admin(message.author):
	args = message.content.split()
	links = str(message.attachments[0].url) if message.attachments else ''
	print(args)
	print(links)

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
					value = '{} {}'.format(' '.join(args[1:]), links),
					links = links,
				)
			conn.execute(ins)
			importCustomCommands(message.guild.id)
			banner = Embed(title='Updated `{}`'.format(args[0], description=' '.join(args[1:])))
			return banner
		else:
			ins = Commands.insert().values(
				id = message.id,
				guild_id = message.guild.id,
				guild_name = message.guild.name,
				name = args[0],
				value = '{} {}'.format(' '.join(args[1:]), links),
				embed = links,
			)
			conn.execute(ins)
			importCustomCommands(message.guild.id)
			banner = Embed(title='Added custom command `{}`'.format(args[0]), description=' '.join(args[1:]))
			return banner

@debug
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
                importCustomCommands(message.guild.id)
            else:
                return 'Command `{}` does not exist.'.format(args[0])


def getHelp(message):
    """
    Get the command help file from ./docs/help
    :param message: <Discord.message object>
    :return: <String> Containing help for the user's available options or list of locations
    """
    incrementUsage(message.guild, 'help')
    custom = ''
    try:
        guildCommands = customCommands[message.guild.id]
        banner = Embed(title='Custom Command Help', description=fetchFile('help', 'custom'))
        for name, value in guildCommands.items():
            custom = '{}`{}`: {}\n'.format(custom, name, value)
        banner.add_field(name='Custom commands available in this server are:', value=custom)
        return None, banner
    except:
        pass


setup()
