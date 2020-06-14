#!/usr/bin/python3

import random

import pendulum
from sqlalchemy import create_engine, and_, func, update, select, MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile, is_admin

			
def setup():
	global engine, meta, Quotes, Lore, Config
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
	Quotes = Table(
		'famQuotes', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('text', String),
		Column('date', String),
		Column('guild', String),
		Column('guild_name', String),
		)	
	Lore = Table(
		'famLore', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('text', String),
		Column('date', String),
		Column('guild', String),
		)
	meta.create_all(engine)
	print('[+] End Quotes Setup')


def helper(message):
	args = message.content.split()
		
	if args[0] == '!lore':
		if len(args) > 1:
			if args[1] == 'add' and is_admin(message.author):
				return insertQuote(Lore, message)
			elif args[1] == 'help' and is_admin(message.author):
				return getHelp(message.author).split('@LORE')[1]
			else: 
				return getQuote(Lore, message.guild.id, ' '.join(args[1:]))
		else:
			return getQuote(Lore, message.guild.id)
			
	elif len(args) > 1:
		if args[1] == 'help':
			return getHelp(message.author).split('@LORE')[0]
		else:
			return getQuote(Quotes, message.guild.id, ' '.join(args[1:]))
	else:
		return getQuote(Quotes, message.guild.id)
	

def insertQuote(Table, message):
	if Table == None:
		Table = Quotes
	
	config = load_config(message.guild.id)
	if config:
		server_locale = config[2]
		stm = config[7].replace('\\n', '\n')
	else:
		server_locale = 'Asia/Tokyo'
		stm = 'Added: "{}" by {} on {}'
	date = pendulum.now(tz=server_locale).to_day_datetime_string()
	
	text = message.content
	for each in message.mentions:
		text = text.replace('<@!{}>'.format(each.id), each.name)
	for each in message.role_mentions:
		text = text.replace('<@&{}>'.format(each.id), each.name)
	args = text.split()	
	
	with engine.connect() as conn:
		if Table.name == 'famQuotes':
			ins = Table.insert().values(
				id = message.id,
				name = message.author.name,
				text = text,
				date = date,
				guild = str(message.guild.id),
				guild_name = message.guild.name,
			)
			conn.execute(ins)
			return stm.format(text, message.author.name, date)
		elif Table.name == 'famLore':
			ins = Table.insert().values(
				id = message.id,
				name = args[2],
				text = ' '.join(args[3:]),
				date = date,
				guild = str(message.guild.id),
				#guild_name = message.guild.name,
			)
			conn.execute(ins)
			return stm.format(' '.join(args[3:]), args[2], date)


def getQuote(Table, guild_, id_=None):
	if Table == None:
		Table = Quotes
	if id_:
		select_st = select([Table]).where(and_(
			Table.c.name == id_,
			Table.c.guild == guild_)).order_by(func.random())
	else:
		select_st = select([Table]).where(
			Table.c.guild == guild_).order_by(func.random())
			
	with engine.connect() as conn:
		result = conn.execute(select_st).fetchone()
		if result:
			config = load_config(guild_)
			if config:			
				if(Table.name == 'famQuotes'):
					stm = config[4].replace('\\n', '\n')
				elif(Table.name == 'famLore'):
					stm = config[5].replace('\\n', '\n')
			else:	
				if(Table.name == 'famQuotes'):
					stm = '{}\n ---{} on {}'
				elif(Table.name == 'famLore'):
					stm = '{}\n ---Scribed by the Lore Master {}, on the blessed day of {}'
			#result[1]: author, [2]: quote, [3]: date
			return stm.format(result[2], result[1], result[3])


def deleteQuote(guild_, id_):
	with engine.connect() as conn:
		for Table in {Quotes, Lore}:
			ins = Table.delete().where(and_(
				Table.c.id == id_,
				Table.c.guild == guild_))
			conn.execute(ins)
	if not checkExists(guild_, id_):
		return 'Deleted quote {}'.format(id_)
	return 'Error'


def checkExists(guild_, id_):
	with engine.connect() as conn:
		select_st = select([Quotes]).where(and_(
			Quotes.c.id == id_,
			Quotes.c.guild == guild_))
		if conn.execute(select_st).fetchall(): return True
	return False	
	
	
def load_config(guild):
	with engine.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild)
		result = conn.execute(select_st).fetchone()
	if result:
		return result
	return None


def getHelp(author):
	banner = fetchFile('help', 'quotes')
	if not is_admin(author):
		banner = banner.split('For Admins:')[0]
	return banner	
	
	
setup()

