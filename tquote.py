#!/usr/bin/python3

import random
from os import listdir, mkdir
from os.path import isdir
import asyncio
import aiohttp
import aiofiles
from pathlib import Path

import pendulum
from sqlalchemy import and_, func, update, select, MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile, is_admin, incrementUsage
from constants import DEFAULT_DIR, ENGINE

			
def setup():
	global meta, Quotes, Lore, Config
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
		Column('embed', String),
		)	
	Lore = Table(
		'famLore', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('text', String),
		Column('date', String),
		Column('guild', String),
		)
	meta.create_all(ENGINE)
	print('[+] End Quotes Setup')


def helper(message):
	text = message.content
	for each in message.mentions:
		text = text.replace('<@!{}>'.format(each.id), each.name)
	args = text.split()
	guild = message.guild.id

	#Lore	
	if args[0] == '!lore':
		incrementUsage(message.guild, 'lore')
		if len(args) > 1:
			if args[1] == 'add' and is_admin(message.author):
				return insertQuote(message, Lore)
			elif args[1] == 'help' and is_admin(message.author):
				return getHelp(message.author).split('@LORE')[1]
			else: 
				return getQuote(guild, Lore, ' '.join(args[1:]))
		else:
			return getQuote(guild, Lore)

	#Quote with options		
	elif len(args) > 1:
		incrementUsage(message.guild, 'quote')
		if args[1] == 'help':
			return getHelp(message.author).split('@LORE')[0]
		else:
			return getQuote(guild, Quotes, ' '.join(args[1:]))
	
	#Any random quote
	else:
		incrementUsage(message.guild, 'quote')
		return getQuote(guild, Quotes)
	

def insertQuote(message, Table):
	"""Insert a quote to the database"""
	if Table is None:
		Table = Quotes
	config = load_config(message.guild.id)
	if config:
		server_locale = config[2]
		stm = config[7].replace('\\n', '\n')
	else:
		server_locale = 'Asia/Tokyo'
		stm = 'Added: "{}" by {} on {}'
	
	#Supress any user or role mentions
	text = message.content
	for each in message.mentions:
		text = text.replace('<@!{}>'.format(each.id), each.name)
	for each in message.role_mentions:
		text = text.replace('<@&{}>'.format(each.id), each.name)
	
	args = text.split()	
	embed = str(message.attachments[0].url) if message.attachments else None
	date = pendulum.now(tz=server_locale).to_day_datetime_string()
	
	with ENGINE.connect() as conn:
		if Table.name == 'famQuotes':
			ins = Table.insert().values(
				id = message.id,
				name = message.author.name,
				text = text,
				date = date,
				guild = str(message.guild.id),
				guild_name = message.guild.name,
				embed = embed,
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


def getQuote(guild, Table, username=None):
	"""Retrive a quote from the database"""
	if username:
		select_st = select([Table]).where(and_(
			Table.c.name == username,
			Table.c.guild == guild)).order_by(func.random())
	else:
		select_st = select([Table]).where(
			Table.c.guild == guild).order_by(func.random())
			
	with ENGINE.connect() as conn:
		result = conn.execute(select_st).fetchone()
		if result:
			config = load_config(guild)
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
			#Check if there is an attached img or file to send as well
			if len(result) > 6 and result[6]:
				stm = stm + '\n' + result[6]
			#Result fields translate as
			#[1]: author, [2]: quote, [3]: date, [6]: embed url
			return stm.format(result[2], result[1], result[3])


def deleteQuote(guild, msg_id):
	"""Remove a quote from the database"""
	with ENGINE.connect() as conn:
		for Table in {Quotes, Lore}:
			select_st = select([Table]).where(and_(
				Table.c.id == msg_id,
				Table.c.guild == guild
			))
			result = conn.execute(select_st).fetchone()
			if result:
				quote = '{}\n ---{} on {}'.format(result[2], result[1], result[3])

				ins = Table.delete().where(and_(
					Table.c.id == msg_id,
					Table.c.guild == guild
					))
				conn.execute(ins)

				#Sanity check
				if not checkExists(guild, msg_id):
					return 'Deleted quote:\n`{}`'.format(quote)


def checkExists(guild, msg_id):
	"""Ensure that we do not add the same message to the database multiple times"""
	with ENGINE.connect() as conn:
		select_st = select([Quotes]).where(and_(
			Quotes.c.id == msg_id,
			Quotes.c.guild == guild))
		if conn.execute(select_st).fetchall(): return True
	return False	


def getReact(message, nsfw):
	"""Get a random gif file from ./emotes or the servers folder"""
	incrementUsage(message.guild, 'gif')

	guild = message.guild.id
	reacts = ['{}/emotes/{}'.format(DEFAULT_DIR, each) for each in listdir('./emotes')]
	
	if isdir('{}/emotes/{}'.format(DEFAULT_DIR, guild)):
		reacts.extend(['{}/emotes/{}/{}'.format(DEFAULT_DIR, guild, each) for each in listdir('./emotes/{}'.format(guild))])
	
	if nsfw and isdir('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, guild)):
		reacts.extend(['{}/emotes/{}/nsfw/{}'.format(DEFAULT_DIR, guild, each) for each in listdir('./emotes/{}/nsfw'.format(guild))])

	return random.choice(reacts)


async def fetchReact(message):
	"""Save a gif a user added with !gif add"""
	incrementUsage(message.guild, 'gif')
	url = str(message.attachments[0].url)
	ext = str(url.split('.')[-1].lower())
    
	if ext != 'gif':
		return 'File must be a gif'
        
	fileName = str(url.split('/')[-1])    
	nsfw = True if 'nsfw' in message.content.lower() else False
    
	if nsfw:
		Path('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, message.guild.id)).mkdir(parents=True, exist_ok=True)    
		filePath = '{}/emotes/{}/nsfw/{}'.format(DEFAULT_DIR, message.guild.id, fileName)
	else:
		Path('{}/emotes/{}'.format(DEFAULT_DIR, message.guild.id)).mkdir(parents=True, exist_ok=True)    
		filePath = '{}/emotes/{}/{}'.format(DEFAULT_DIR, message.guild.id, fileName)
    
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200:
				f = await aiofiles.open(filePath, mode='wb')
				await f.write(await resp.read())
				await f.close()
				print("[+] Saved: {}".format(filePath))  
	
	
def load_config(guild):
	with ENGINE.connect() as conn:
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

