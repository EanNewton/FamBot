#!/usr/bin/python3

import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path

import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
extSet = {}


def setup():
	global engine, meta, Corpus
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
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
	meta.create_all(engine)
	for file_ in {'audio', 'docs', 'images', 'video'}:
		f = fetchFile('ext', file_).strip('\n')
		extSet[file_] = f.split()
	print('[+] End Logger Setup')


def corpusInsert(message, timeStamp):
	# mMentions = [''.join(str(each)) for each in message.mentions if message.mentions]
	# mEmbeds = [''.join(str(each.to_dict())) for each in message.embeds if message.embeds]
	# mAttach = [''.join(str(each.filename)) for each in message.attachments if message.attachments]
	# mChanMentions = [''.join(str(each)) for each in message.channel_mentions if message.channel_mentions]
	# mRoleMentions = [''.join(str(each)) for each in message.role_mentions if message.role_mentions]
	mMentions = [''.join(str(each)) for each in message.mentions]
	mEmbeds = [''.join(str(each.to_dict())) for each in message.embeds]
	mAttach = [''.join(str(each.filename)) for each in message.attachments]
	mChanMentions = [''.join(str(each)) for each in message.channel_mentions]
	mRoleMentions = [''.join(str(each)) for each in message.role_mentions]

	with engine.connect() as conn:
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
	url = str(message.attachments[0].url)
	ext = str(url.split('.')[-1].lower())
	[await fetcher(each, url, time, message) for each in extSet if ext in extSet[each]]

	
setup()
