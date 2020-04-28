#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, fetchFile
from sqlalchemy import create_engine, update, select, MetaData, Table, Column, Integer, String 


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

blacklistLow = {"jap"}
blacklistStrict = {"xxx"}

def check(message):
	text = message.content.split()
	fLevel = alch_getFilter(message.channel.id)
	lists = {2: (blacklistStrict), 1: (blacklistLow)}
	if fLevel:
		fLevel = fLevel[0][1]
	else:
		return False
	if fLevel in lists:
		for word in text:
			if word in lists[fLevel]:
				return True
	return False

def importBlacklists():
	listOfFiles_low = list()
	listOfFiles_high = list()
	for (dirpath, dirnames, filenames) in os.walk(DEFAULT_DIR+'/blacklists'):
		if 'low' in dirpath:
			listOfFiles_low += [os.path.join(dirpath, file) for file in filenames]
		if 'strict' in dirpath:
			listOfFiles_high += [os.path.join(dirpath, file) for file in filenames]
	
	for file_ in listOfFiles_low:
		with open(file_, 'r') as f:
			for line in f:
				blacklistLow.add(line.strip())
				blacklistStrict.add(line.strip())
	for file_ in listOfFiles_high:
		with open(file_, 'r') as f:
			for line in f:
				blacklistStrict.add(line.strip())
	blacklistStrict.remove('')
	print("[+] Imported Filter Blacklists")
	return True

def addWord(level, word):
	fileDict = {
		'1': DEFAULT_DIR+'/blacklists/low/blacklist_custom.txt',
		'2': DEFAULT_DIR+'/blacklists/strict/blacklist_custom.txt',
		}
	path = fileDict.get(level, None)
	word = ' '.join(word)
	if path:
		with open(path, 'a') as f:
			f.write(word)
			print("[+] Added "+word+" to level "+level+" custom filters")
			return "Success, added: `"+word+"` to Filter level "+level
	return "Error"

def alch_insertFilter(id_, level):
	conn = engine.connect()
	exists = alch_getFilter(id_)
	if exists:
		ins = Filters.update().where(Filters.c.id==id_).values(level=level)	
	else:
		ins = Filters.insert().values(id = id_, level = level,)
	conn.execute(ins)
	return "Set filter for current channel to "+str(level)

def alch_getFilter(id_):
	select_st = select([Filters]).where(
		Filters.c.id == id_)
	conn = engine.connect()	
	res = conn.execute(select_st)
	result = res.fetchall()
	if result:
		return result
	else:
		return None

def alch_reset():
	conn = engine.connect()
	query = Filters.drop(engine)
	setup()
	print("[!] TABLE filters RESET")

def setup():
	global engine
	global meta
	global Filters
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
	meta = MetaData()
	Filters = Table(
		'filters', meta,
		Column('id', Integer, primary_key = True),
		Column('level', Integer),
		)
	meta.create_all(engine)
	print('[+] End filters Setup')
	
def helper(message):
	args = message.content.split()
	operator = args[1].lower()
	return {
		'get': lambda: alch_getFilter(message.channel.id),
		'set': lambda: alch_insertFilter(message.channel.id, args[2]),
		'clear': lambda: alch_insertFilter(message.channel.id, 0),
		'clearall': lambda: alch_reset(),
		'help': lambda: get_help(),
		'add': lambda: addWord(args[2], args[3:]),
	}.get(operator, lambda: None)()

def get_help():
	return fetchFile('help', 'filters')

setup()
