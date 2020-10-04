#!/usr/bin/python3

import os
from sqlalchemy import update, insert, select, and_
from sqlalchemy import MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile, fetch_value, guildList, is_admin, incrementUsage
from constants import DEFAULT_DIR, ENGINE

blacklistLow = set()
blacklistStrict = set()
blacklistCustom = dict()


def setup():
	global meta, Filters
	meta = MetaData()
	Filters = Table(
		'filters', meta,
		Column('id', Integer, primary_key = True),
		Column('level', Integer),
		Column('guild_id', String),
		)
	meta.create_all(ENGINE)
	importBlacklists()
	print('[+] End filters Setup')


def helper(message):
	incrementUsage(message.guild, 'filter')
	if is_admin(message.author):
		args = message.content.split()
		operator = args[1].lower() if len(args) > 1 else 'help'
		return {
			'get': lambda: getFilter(message),
			'set': lambda: insertFilter(message, args[2]),
			'clear': lambda: insertFilter(message, 0),
			'help': lambda: getHelp(),
		}.get(operator, lambda: None)()

@debug
def check(message):
	"""Check if message violates filter for current channel"""
	text = message.content.split()
	fLevel = getFilter(message)
	custom = blacklistCustom[str(message.guild.id)]
	lists = {'2': (blacklistStrict), '1': (blacklistLow), '3': (custom)}
		
	if fLevel in lists:
		for word in text:
			if word in lists[fLevel]:
				return True 
	return False 


def importBlacklists():
	"""Scan local docs folder for banned words"""
	listOfFiles_low = list()
	listOfFiles_high = list()
	
	for (dirpath, _, filenames) in os.walk(DEFAULT_DIR+'/docs/blacklists'):
		if 'low' in dirpath:
			listOfFiles_low += [os.path.join(dirpath, file_) for file_ in filenames]
		elif 'strict' in dirpath:
			listOfFiles_high += [os.path.join(dirpath, file_) for file_ in filenames]
	
	for file_ in listOfFiles_low:
		with open(file_, 'r') as f:
			for line in f:
				blacklistLow.add(line.strip())
				blacklistStrict.add(line.strip())
	for file_ in listOfFiles_high:
		with open(file_, 'r') as f:
			for line in f:
				blacklistStrict.add(line.strip())
	for each in guildList():
		importCustom(each)
			
	blacklistStrict.remove('')
	print("[+] Imported Filter Blacklists")


#TODO ensure is splitting values from result instead of single long str
def importCustom(guild):
	"""Get any banned words from uploaded config file"""
	result = fetch_value(guild, 8)
	if result:
		blacklistCustom[str(guild)] = set(result)
	else:
		blacklistCustom[str(guild)] = None


def insertFilter(message, level):
	"""Set filter for current channel in database"""
	with ENGINE.connect() as conn:
		if getFilter(message):
			ins = Filters.update().where(and_(
				Filters.c.id == message.channel.id,
				Filters.c.guild_id == message.guild.id,
				)).values(level = level)	
		else:
			ins = Filters.insert().values(
				id = message.channel.id,
				level = level,
				guild_id = str(message.guild.id),
				)
		conn.execute(ins)
		importBlacklists()
		importCustom(message.guild.id)
	return "Set filter for current channel to {}".format(level)


def getFilter(message):
	"""Retrieve filter level from database"""
	with ENGINE.connect() as conn:
		select_st = select([Filters]).where(and_(
			Filters.c.id == message.channel.id,
			Filters.c.guild_id == message.guild.id
			))
		result = conn.execute(select_st).fetchone()
		if result:
			return result[1]


def getHelp():
	return fetchFile('help', 'filters')

setup()
