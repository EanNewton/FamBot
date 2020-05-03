#!/usr/bin/python3

import random
from discordUtils import debug, fetchFile, is_admin
from sqlalchemy import create_engine, func, update, select, MetaData, Table, Column, Integer, String 

@debug	
def helper(args, author):
	if len(args) > 1:
		if args[1] == 'help':
			return get_help(author.roles)
		elif args[1] == 'clearall' and is_admin(author.roles):
			reset()
		else:
			return getQuote(args[1])
	else:
		return getQuote()	

def getHelp(author):
	banner = fetchFile('help', 'quotes')
	if is_admin(author.roles):
		banner += "React to a message with ❌ to remove it."
	return banner		
				
def setup():
	global engine, meta, Quotes
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
	meta = MetaData()
	Quotes = Table(
		'famQuotes', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('text', String),
		Column('date', String),
		)
	meta.create_all(engine)
	print('[+] End quotes Setup')

def reset():
	conn = engine.connect()
	query = Quotes.drop(engine)
	setup()
	print("[!] TABLE schedule RESET")
	
def insertQuote(entity):
	(id_, name, text, date) = entity
	conn = engine.connect()
	ins = Quotes.insert().values(
		id = id_,
		name = name,
		text = text,
		date = date,
	)
	conn.execute(ins)
	return 'Added: "{}" by {} on {}'.format(text, name, date)

def getQuote(id_=None):
	if id_:
		select_st = select([Quotes]).where(Quotes.c.name == id_).order_by(func.random())
	else:
		select_st = select([Quotes]).order_by(func.random())
	conn = engine.connect()	
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		#result[1]: author, [2]: quote, [3]: date
		return '{}\n ---{} on {}'.format(result[1], result[2], result[3])

def deleteQuote(id_):
	conn = engine.connect()
	ins = Quotes.delete().where(Quotes.c.id == id_,)
	conn.execute(ins)
	return "Deleted quote"

def checkExists(id_):
	conn = engine.connect()	
	select_st = select([Quotes]).where(
		Quotes.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	return result is not None	

setup()
