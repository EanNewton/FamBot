#!/usr/bin/python3

#TODO Add restricted channels
#TODO Add !push to notify guild owners of updates
#TODO Create a GUI config app
#TODO Scheduled commands
#TODO Add option to delete command request message
#TODO Server counts

import json
import functools
import asyncio
import aiohttp
import aiofiles

from sqlalchemy import delete, select, MetaData, Table, Column, Integer, String

from constants import DEFAULT_DIR, jsonFormatter, ENGINE

modRoles = dict()

def setup():
	global meta, Config, Stats
	meta = MetaData()
	Config = Table(
		'config', meta,
		Column('id', Integer, primary_key = True),
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
	updateModRoles()
	print('[+] End Util Setup')

#############################
# General Utility Functions #
#############################
def debug(func):
    """Print the function signature and return value"""
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


def fetchFile(directory, filename):
	"""Safely read in a dynamically designated local file"""
	with open('{}/docs/{}/{}.txt'.format(DEFAULT_DIR, directory, filename), 'r') as f:
		return f.read()


def is_admin(author):
	"""
	Check if a discord user has been given bot admin permissions
	:param athor: <Discord.message.author object>
	:return: <bool>
	"""
	try:
		if author.guild.owner_id == author.id or int(author.id) == 184474309891194880:
			return True
	except: pass
	try:
		for role in author.roles:
			if str(role).lower() in modRoles[author.guild.id]:
				return True
	except: pass
	return False


def wrap(s, w):
	"""Break a long string s into a list of strings of length w"""
	return [s[i:i + w] for i in range(0, len(s), w)]


############################
# Config Utility Functions #
############################
def incrementUsage(guild, command):
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
				raw_messages = dict_['raw_messages'],
				quote = dict_['quote'],
				lore = dict_['lore'],
				wolf = dict_['wolf'],
				wotd = dict_['wotd'],
				dict = dict_['dict'],
				trans = dict_['trans'],
				google = dict_['google'],
				config = dict_['config'],
				sched = dict_['sched'],
				filter = dict_['filter'],
				doip = dict_['doip'],
				gif = dict_['gif'],
				stats = dict_['stats'],
				eight = dict_['eight'],
				help = dict_['help'],
				custom = dict_['custom'],
			)
			conn.execute(ins)
			return 1

		else:
			print('[+] Creating usage counter for {}'.format(guild.name))
			ins = Stats.insert().values(
				id = guild.id,
				guild_name = guild.name,
				raw_messages = 0,
				quote = 0,
				lore = 0,
				wolf = 0,
				wotd = 0,
				dict = 0,
				trans = 0,
				google = 0,
				config = 0,
				sched = 0,
				filter = 0,
				doip = 0,
				gif = 0,
				stats = 0,
				eight = 0,
				help = 0,
				custom = 0,
			)
			conn.execute(ins)
			return incrementUsage(guild, command)


def config_helper(message):
	"""
	Create or reset the server config entry
	:param message: <Discord.message object>
	:return: <String> Describing file location
	"""
	incrementUsage(message.guild, 'config')
	if is_admin(message.author):	
		args = message.content.split()
		if len(args) > 1 and args[1] == 'reset':
			return config_reset(message.guild)
		else:
			return config_create(message.guild)


def updateModRoles():
	"""
	Sync in-memory mod roles with database values for all guilds
	:return: <None>
	"""
	for guild in guildList():
		roles = fetch_value(guild, 9, ';')
		if roles:
			modRoles[guild] = [str(role).lower() for role in roles]


def config_create(guild):
	"""
	Get the config file for the server and give to the user
	:param guild: <Discord.guild object>
	:return: <String> Describing file location
	"""
	with ENGINE.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild.id)
		result = conn.execute(select_st).fetchone()
		
		if result:
			print('[+] Found guild config for {}'.format(guild.name))
			#Create an in-memory version of the config
			columns = []
			for each in Config.c:
				columns.append(each.name)
			dict_ = dict(zip(columns, result))
			
			#For pretty printing, make the user's life easier
			for each in jsonFormatter[0]:
				dict_['schedule'] = dict_['schedule'].replace(each[0], each[1])
			for each in jsonFormatter[1]:
				dict_[each[1]] = dict_.pop(each[0])
				
			with open('{}/docs/config/{}.json'.format(DEFAULT_DIR, guild.id), 'w') as f:
				json.dump(dict_, f, indent=4)
				f.write('\n\n{}'.format(fetchFile('help', 'config')))	
			return '{}/docs/config/{}.json'.format(DEFAULT_DIR, guild.id)		
		
		else:
			#Guild has no config entry, create one and try again
			config_createDefault(guild)
			return config_create(guild)


def config_createDefault(guild):
	"""
	Create a new default entry for the given guild
	:param guild: <Discord.guild object>
	:return: <None>
	"""
	print('[+] Creating new guild config for {}'.format(guild.name))
	with ENGINE.connect() as conn:
		ins = Config.insert().values(
			id = guild.id,
			guild_name = guild.name,
			locale = 'Asia/Tokyo',
			schedule = '0=10,17:15;1=10,12;2=16,10:15;3=2:44;4=10;5=16:30;',
			quote_format = '{0}\n ---{1} on {2}',
			lore_format = '{0}\n ---Scribed by the Lore Master {1}, on the blessed day of {2}',
			url = 'Come hang with us at: <https://www.twitch.tv/>',
			qAdd_format = 'Added:\n "{0}"\n by {1} on {2}',
			filtered = 'none',
			mod_roles = 'mod;admin;discord mod;',
			anonymous = 1,
			)		
		conn.execute(ins)


def config_load(guild):
	"""
	Load the JSON file supplied by user into the database
	:param guild: <Int> Discord guild ID
	:return: <None>
	"""
	#Undo the pretty printing
	with open('{}/docs/config/{}.json'.format(DEFAULT_DIR, guild), 'r') as f:
		dict_ = json.loads(f.read().split('```', maxsplit=1)[0])
	for each in jsonFormatter[1]:		
		dict_[each[0]] = dict_.pop(each[1])
	for each in jsonFormatter[0]:
		dict_['schedule'] = dict_['schedule'].replace(each[1], each[0])
	
	with ENGINE.connect() as conn:
		ins = Config.update().where(Config.c.id == guild).values(
					locale = dict_['locale'],
					schedule = dict_['schedule'],
					quote_format = dict_['quote_format'],
					lore_format = dict_['lore_format'],
					url = dict_['url'],
					qAdd_format = dict_['qAdd_format'],
					filtered = dict_['filtered'],
					mod_roles = dict_['mod_roles'],
					anonymous = dict_['anonymous'],
					)
		conn.execute(ins)
	#TODO ensure to lower
	modRoles[guild] = fetch_value(guild, 9, ';')
	print('[+] Loaded new config for {}'.format(guild.name))
		

def config_reset(guild):
	"""
	Return the config to default values
	:param guild: <Discord.guild object>
	:return: <None>
	"""
	with ENGINE.connect() as conn:
		ins = Config.delete().where(Config.c.id == guild.id)
		conn.execute(ins)
	print('[+] Reset config for: {}'.format(guild.name))
	return config_create(guild)


async def config_fetchEmbed(message):
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
				print('[+] Saved: {}'.format(filePath))	

	config_load(message.guild.id)	
	
	
def fetch_value(guild, val, delim=None):
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
		result = result[val].split(delim)
		result[:] = (val for val in result if val not in {'', ' ', '\n', None})
		return result

	
def guildList():
	"""
	Get a list of all guilds ids
	:return: <List> IDs for all guilds the bot is active in
	"""
	with ENGINE.connect() as conn:
		select_st = select([Config])
		res = conn.execute(select_st)
		result = res.fetchall()

	return [each[0] for each in result]
	
setup()
