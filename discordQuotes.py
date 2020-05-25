#!/usr/bin/python3

import random
import pendulum
from discordUtils import debug, fetchFile, writeFile, is_admin
from sqlalchemy import create_engine, and_, func, update, select, MetaData, Table, Column, Integer, String 



def helper(message):
	args = message.content.split()
		
	if args[0] == '!lore':
		if len(args) > 1:
			if args[1] == 'add' and is_admin(message.author.roles):
				config = load_config(message.guild.id)
				if config:
					server_locale = config[2]
				else:
					server_locale = 'Asia/Tokyo'
				dateTime = pendulum.now(tz=server_locale)
				entity = [
					message.id, 
					args[2],
					' '.join(args[3:]), 
					str(dateTime.to_formatted_date_string()),
					str(message.guild.id),
				]	
				return insertQuote(Lore, entity)
			else: 
				return getQuote(Lore, message.guild.id, ' '.join(args[1:]))
		else:
			return getQuote(Lore, message.guild.id)
			
	elif len(args) > 1:
		if args[1] == 'help':
			return getHelp(message.author)
		else:
			return getQuote(Quotes, message.guild.id, ' '.join(args[1:]))
	else:
		return getQuote(Quotes, message.guild.id)


def getHelp(author):
	banner = fetchFile('help', 'quotes')
	if is_admin(author.roles):
		banner += "React to a message with ❌ to remove it."
	return banner		
				
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
		Column('sched_format', String),
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
	dateTime = pendulum.now(tz=server_locale)
	text = message.content
	for each in message.mentions:
		text = text.replace('<@!'+str(each.id)+'>', each.name)

	name = str(message.author)[:-5]
	date = str(dateTime.to_day_datetime_string())
	conn = engine.connect()
	ins = Table.insert().values(
		id = message.id,
		name = name,
		text = text,
		date = date,
		guild = str(message.guild.id),
		guild_name = message.guild.name,
	)
	conn.execute(ins)
	return stm.format(text, name, date)


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
	conn = engine.connect()	
	res = conn.execute(select_st)
	result = res.fetchone()
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
	conn = engine.connect()
	for Table in {Quotes, Lore}:
		ins = Table.delete().where(and_(
		Table.c.id == id_,
		Table.c.guild == guild_))
		conn.execute(ins)
	return "Deleted quote"


def checkExists(guild_, id_):
	conn = engine.connect()	
	select_st = select([Quotes]).where(and_(
		Quotes.c.id == id_,
		Quotes.c.guild == guild_)
		)
	res = conn.execute(select_st)
	result = res.fetchall()
	return result is not None	

		
def load_config(guild):
	conn = engine.connect()	
	select_st = select([Config]).where(Config.c.id == guild)
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result
	return None

setup()

'''
def reset():
	conn = engine.connect()
	query = Quotes.drop(engine)
	setup()
	print("[!] TABLE schedule RESET")
'''
