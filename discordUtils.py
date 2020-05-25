#!/usr/bin/python3

import functools
import os
import json
from sqlalchemy import delete, create_engine, select, MetaData, Table, Column, Integer, String

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
adminRoles = {'admin', 'mod', 'discord mod'}

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
		)
	meta.create_all(engine)
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


def writeFile(directory, filename, text):
	with open(DEFAULT_DIR+'/docs/'+directory+'/'+str(filename)+'.json', 'w') as f:
		json.dump(text, f)

def fetchFile(directory, filename):
	with open(DEFAULT_DIR+'/docs/'+directory+'/'+filename+'.txt', 'r') as f:
		return f.read()


def is_admin(roles):
	for role in roles:
		if str(role).lower() in adminRoles:
			return True
	else: return False

def is_bot(roles):
	for role in roles:
		if str(role).lower() == 'bot':
			return True
	else: return False


def create_config(guild):
	conn = engine.connect()	
	select_st = select([Config]).where(Config.c.id == guild.id)
	res = conn.execute(select_st)
	result = res.fetchone()
	columns = []
	keys = []
	if result:
		for each in Config.c:
			columns.append(each.name)
		for each in result:
			keys.append(each)
		dict_ = dict(zip(columns, keys))
		dict_['schedule'] = dict_['schedule'].replace('0=', 'Monday = ')
		dict_['schedule'] = dict_['schedule'].replace('1=', 'Tuesday = ')
		dict_['schedule'] = dict_['schedule'].replace('2=', 'Wednesday = ')
		dict_['schedule'] = dict_['schedule'].replace('3=', 'Thursday = ')
		dict_['schedule'] = dict_['schedule'].replace('4=', 'Friday = ')
		dict_['schedule'] = dict_['schedule'].replace('5=', 'Saturday = ')
		dict_['schedule'] = dict_['schedule'].replace('6=', 'Sunday = ')
		dict_['schedule'] = dict_['schedule'].replace(',', ', ')
		dict_['schedule'] = dict_['schedule'].replace(';', '; ')
		writeFile('config', guild.id, dict_)
		banner = [fetchFile('help', 'config'), '{}/docs/config/{}.json'.format(DEFAULT_DIR, str(guild.id))]
		return banner
	else:
		ins = Config.insert().values(
			id = guild.id,
			guild_name = guild.name,
			locale = 'Asia/Tokyo',
			schedule = '0=10,17:15;1=10,12;2=16,10:15;3=2:44;4=10;5=16:30;',
			quote_format = '{}\n ---{} on {}',
			lore_format = '{}\n ---Scribed by the Lore Master {}, on the blessed day of {}',
			url = 'https://www.twitch.tv/',
			qAdd_format = 'Added: `{}` by {} on {}',
		)		
		res = conn.execute(ins)
		return create_config(guild)


def load_config(guild):
	filePath = '{}/docs/config/{}.json'.format(DEFAULT_DIR, guild)
	with open(filePath, 'r') as f:
		dict_ = json.load(f)
		dict_['schedule'] = dict_['schedule'].replace('Monday = ', '0=')
		dict_['schedule'] = dict_['schedule'].replace('Tuesday = ', '1=')
		dict_['schedule'] = dict_['schedule'].replace('Wednesday = ', '2=')
		dict_['schedule'] = dict_['schedule'].replace('Thursday = ', '3=')
		dict_['schedule'] = dict_['schedule'].replace('Friday = ', '4=')
		dict_['schedule'] = dict_['schedule'].replace('Saturday = ', '5=')
		dict_['schedule'] = dict_['schedule'].replace('Sunday = ', '6=')
		dict_['schedule'] = dict_['schedule'].replace(', ', ',')
		dict_['schedule'] = dict_['schedule'].replace('; ', ';')
		conn = engine.connect()	
		ins = Config.update().where(Config.c.id==guild).values(
					locale = dict_['locale'],
					schedule = dict_['schedule'],
					quote_format = dict_['quote_format'],
					lore_format = dict_['lore_format'],
					url = dict_['url'],
					qAdd_format = dict_['qAdd_format'],
				)
		results = conn.execute(ins)
		return True
		

def reset_config(guild):
	conn = engine.connect()
	ins = Config.delete().where(Config.c.id == guild.id)
	results = conn.execute(ins)
	return create_config(guild)
setup()
