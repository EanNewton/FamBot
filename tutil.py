#!/usr/bin/python3
#TODO Set config file {} to order independent 

import os
import json
import functools
import asyncio
import aiohttp
import aiofiles

from sqlalchemy import delete, create_engine, select, MetaData, Table, Column, Integer, String


DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
adminRoles = [
	'admin', 
	'mod', 
	'discord mod'
	]
modRoles = dict()
jsonFormatter = [[
		['0=', 'Monday = '],
		['1=', 'Tuesday = '],
		['2=', 'Wednesday = '],
		['3=', 'Thursday = '],
		['4=', 'Friday = '],
		['5=', 'Saturday = '],
		['6=', 'Sunday = '],
		[',', ', '],
		[';', '; '],
	],[
		['id', 'Server ID'],
		['guild_name', 'Server Name'],
		['locale', 'Server Locale'],
		['schedule', 'Schedule'],
		['url', 'URL Footer'],
		['quote_format', 'Quote Format'],
		['qAdd_format', 'Quote Added Format'],
		['lore_format', 'Lore Format'],
		['filtered', 'Blacklisted Words'],
		['mod_roles', 'Moderator Roles'],
	]]


def setup():
	global engine, meta, Config
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
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
		)
	meta.create_all(engine)
	
	for guild in guildList():
		modRoles[guild] = fetch_value(guild, 9, ';')		
	
	print('[+] End Util Setup')


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
	with open('{}/docs/{}/{}.txt'.format(DEFAULT_DIR, directory, filename), 'r') as f:
		return f.read()

@debug
def is_admin(author):
	print(modRoles[author.guild.id])
	if author.guild.owner.id == author.id:
		return True
	for role in author.roles:
		if str(role).lower() in modRoles[author.guild.id]:
			return True
	return False

@debug
def is_bot(author):
	if author.bot:
		return True
	return False

@debug
def config_create(guild):
	with engine.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild.id)
		result = conn.execute(select_st).fetchone()
		if result:
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
			)		
			conn.execute(ins)
			return config_create(guild)

@debug
def config_load(guild):
	with open('{}/docs/config/{}.json'.format(DEFAULT_DIR, guild), 'r') as f:
		dict_ = json.loads(f.read().split('```', maxsplit=1)[0])
	for each in jsonFormatter[1]:		
		dict_[each[0]] = dict_.pop(each[1])
	for each in jsonFormatter[0]:
		dict_['schedule'] = dict_['schedule'].replace(each[1], each[0])
	
	with engine.connect() as conn:
		ins = Config.update().where(Config.c.id == guild).values(
					locale = dict_['locale'],
					schedule = dict_['schedule'],
					quote_format = dict_['quote_format'],
					lore_format = dict_['lore_format'],
					url = dict_['url'],
					qAdd_format = dict_['qAdd_format'],
					filtered = dict_['filtered'],
					mod_roles = dict_['mod_roles'],
					)
		conn.execute(ins)
	#TODO ensure to lower
	modRoles[guild] = fetch_value(guild, 9, ';')
	print(modRoles)
		

def config_reset(guild):
	with engine.connect() as conn:
		ins = Config.delete().where(Config.c.id == guild.id)
		conn.execute(ins)
	print('[+] Reset config for: {}'.format(guild.name))
	return config_create(guild)


async def config_fetchEmbed(message):
	filePath = '{}/docs/config/{}.json'.format(DEFAULT_DIR, message.guild.id)
	async with aiohttp.ClientSession() as session:
		async with session.get(str(message.attachments[0].url)) as resp:
			if resp.status == 200:
				f = await aiofiles.open(filePath, mode='wb')
				await f.write(await resp.read())
				await f.close()
				print('[+] Saved: {}'.format(filePath))	
	config_load(message.guild.id)	
	

@debug
def fetch_value(guild, val, delim=None):
	with engine.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild)
		res = conn.execute(select_st)
		result = res.fetchone()
	if result and result[val]:
		result = result[val].split(delim)
		result[:] = (val for val in result if val not in {'', ' ', None})
		return result
	return None
	

def guildList():
	with engine.connect() as conn:
		select_st = select([Config])
		res = conn.execute(select_st)
		result = res.fetchall()
	idList = [each[0] for each in result]
	return idList
	
setup()
