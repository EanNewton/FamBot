#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, fetchFile, is_admin
from sqlalchemy import create_engine, func, update, select, MetaData, Table, Column, Integer, String 


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')

			
def setup():
	global engine
	global meta
	global Quotes
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
	
def alch_insertQuote(entity):
	(id_, name, text, date) = entity
	conn = engine.connect()
	ins = Quotes.insert().values(
		id = id_,
		name = name,
		text = text,
		date = date,
	)
	conn.execute(ins)

def alch_getQuote(id_):
	conn = engine.connect()	
	if id_ == -1:
		select_st = select([Quotes]).order_by(func.random())
	else:
		select_st = select([Quotes]).where(Quotes.c.name == id_).order_by(func.random())
	res = conn.execute(select_st)
	result = res.fetchone()
	print(result)
	if result:
		author = result[1]
		quote = result[2]
		date = result[3]
		return str(quote) + '\n ---' + str(author) + ' on ' + str(date)
	else:
		return None	

def alch_reset():
	conn = engine.connect()
	query = Quotes.drop(engine)
	setup()
	print("[!] TABLE schedule RESET")

def alch_deleteQuote(id_):
	conn = engine.connect()
	ins = Quotes.delete().where(Quotes.c.id == id_,)
	conn.execute(ins)
	return "Deleted quote"

def alch_checkExists(id_):
	conn = engine.connect()	
	select_st = select([Quotes]).where(
		Quotes.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	if result:
		return True
	else:
		return False	
		
def get_help(author):
	banner = fetchFile('help', 'quotes')
	if is_admin(author.roles):
		banner += "React to a message with ❌ to remove it."
	return banner
	
def helper(args, author):
	if len(args) > 1:
		if args[1] == 'help':
			return get_help(author.roles)
		elif args[1] == 'clearall' and is_admin(author.roles):
			alch_reset()
		else:
			return alch_getQuote(args[1])
	else:
		return alch_getQuote(-1)

setup()
