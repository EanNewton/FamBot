#!/usr/bin/python3

#TODO Add method for admins to get a log of a user, channel, or guild

import aiohttp
import aiofiles
from pathlib import Path

import pendulum
import pandas as pd
import xlsxwriter
from sqlalchemy import MetaData, Table, Column, Integer, String, select

from tutil import debug, fetchFile, is_admin, config_fetchEmbed
from tfilter import importCustom
from constants import DEFAULT_DIR, ENGINE

extSet = {}


def setup():
	global meta, Corpus
	meta = MetaData()
	Corpus = Table(
		'corpus', meta,
		Column('id', Integer, primary_key = True),
		Column('content', String),
		Column('user_name', String),
		Column('user_id', String),
		Column('time', String),
		Column('channel', String),
		Column('embeds', String),
		Column('attachments', String),
		Column('mentions', String),
		Column('channel_mentions', String),
		Column('role_mentions', String),
		Column('msg_id', String),
		Column('reactions', String),
		Column('guild', String),
		Column('guild_name', String),
		)
	meta.create_all(ENGINE)
	for file_ in {'audio', 'docs', 'images', 'video'}:
		f = fetchFile('ext', file_).strip('\n')
		extSet[file_] = f.split()
	print('[+] End Logger Setup')


async def logMessage(message):
	"""
	Grab new config file if present and add each raw message to the database. 
	:param message: <Discord.message object>
	:return: <None>
	"""
	timestamp = pendulum.now(tz='Asia/Tokyo').to_datetime_string()
	corpusInsert(message, timestamp)
	
	if message.attachments:
		await fetchEmbed(message, timestamp)
		if is_admin(message.author) and message.attachments[0].filename == '{}.json'.format(message.guild.id):
			await config_fetchEmbed(message)
			importCustom(message.guild.id)


def corpusInsert(message, timeStamp):
	"""
	For bulk logging of all messages sent in all servers. Used for stats and admin logs.
	:param message: <Discord.message object>
	:param timeStamp> <String> The current server time
	:return: <None>
	"""
	mMentions = [''.join(str(each)) for each in message.mentions]
	mEmbeds = [''.join(str(each.to_dict())) for each in message.embeds]
	mAttach = [''.join(str(each.filename)) for each in message.attachments]
	mChanMentions = [''.join(str(each)) for each in message.channel_mentions]
	mRoleMentions = [''.join(str(each)) for each in message.role_mentions]

	with ENGINE.connect() as conn:
		ins = Corpus.insert().values(
			content = str(message.content),
			user_name = str(message.author),
			user_id = str(message.author.id),
			time = str(timeStamp),
			channel = str(message.channel),
			embeds = str(mEmbeds),
			attachments = str(mAttach),
			mentions = str(mMentions),
			channel_mentions = str(mChanMentions),
			role_mentions = str(mRoleMentions),
			msg_id = str(message.id),
			reactions = "none",
			guild = str(message.guild.id),
			guild_name = str(message.guild.name),
			)
		conn.execute(ins)


async def fetcher(filetype, url, time, message):
	"""
	Internal function to download any message attachments from Discord servers
	:param filetype: <String> The file extension
	:param url: <String> The file location URL
	:param time: <String> Current server time
	:param message: <Discord.message object>
	:return: <None>
	"""
	fileName = '{}_{}_{}'.format(message.author.name, time, url.split('/')[-1])	
	Path('{}/log/{}/{}/{}'.format(
		DEFAULT_DIR, filetype, message.guild.name, message.channel.name)).mkdir(
		parents=True, exist_ok=True)	
	filePath = '{}/log/{}/{}/{}/{}'.format(
		DEFAULT_DIR, filetype, message.guild.name, message.channel.name, fileName)
		
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200:
				f = await aiofiles.open(filePath, mode='wb')
				await f.write(await resp.read())
				await f.close()
				print("[+] Saved: {}".format(filePath))


async def fetchEmbed(message, time):
	"""
	Call fetcher() for each message.attachment
	:param message: <Discord.message object>
	:param time: <String> Current server time
	:return: <None>
	"""
	url = str(message.attachments[0].url)
	ext = str(url.split('.')[-1].lower())
	[await fetcher(each, url, time, message) for each in extSet if ext in extSet[each]]


def getLog(message):
	"""
	Get an excel file log of a guild
	:param message: <Discord.message object>
	:return: <List> Describing output and file location
	"""
	select_st = select([Corpus]).where(
		Corpus.c.guild == message.guild.id)
	df = [None]
	with ENGINE.connect() as conn:
		result = conn.execute(select_st).fetchall()
		keys = conn.execute(select_st).keys()

		entries = [each.values() for each in result]
		for each in entries:
			each[0] = 'id_{}'.format(each[0])
			each[3] = 'uid_{}'.format(each[3])
			each[11] = 'mid_{}'.format(each[11])
			each[13] = 'gid_{}'.format(each[13])

		df[0] = pd.DataFrame(entries, columns=keys)
	with pd.ExcelWriter('{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id), engine='xlsxwriter') as writer:
		df[0].to_excel(writer, sheet_name='Messages')
	return ['Log of all messages for this guild:', '{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id)]


#Placeholder function
def getHelp(message):
	"""
	Get the help file in ./docs/help for admin command to get a log file
	:param message: <Discord.message object>
	:return: <String> The local help file
	"""
	pass


setup()
