#!/usr/bin/python3

import sqlalchemy
import asyncio
import aiohttp
import aiofiles
from discordUtils import debug, fetchFile
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String 

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
	importExts()
	print('[+] End Corpus.db Setup')

def importExts():
	listOfFiles = {'audio', 'docs', 'images', 'video'}
	for file_ in listOfFiles:
		f = fetchFile('ext', file_).strip('\n')
		extSet[file_] = f.split()


def corpusInsert(message, timeStamp):
	mChanMentions = ''
	mAttach = ''
	mMentions = ''
	mEmbeds = ''
	mRoleMentions = ''
	
	if message.embeds:
		for each in range(len(message.embeds)):
			mEmbeds += str(message.embeds)
	if message.attachments:
		for each in range(len(message.attachments)):
			mAttach += str(message.attachments[each].filename)
	if message.mentions:
		for each in range(len(message.mentions)):
			mMentions += str(message.mentions[each])
	if message.channel_mentions:
		for each in range(len(message.channel_mentions)):
			mChanMentions += str(message.channel_mentions[each])
	if message.role_mentions:
		for each in range(len(message.role_mentions)):
			mRoleMentions += str(message.role_mentions[each])

	conn = engine.connect()	
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
	result = conn.execute(ins)

async def fetcher(filetype, url, time, author):
	filePath = "./log/"+filetype+"/"+author+"_"+time+"_"+url.split('/')[-1]
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
	for each in extSet:
		if ext in extSet[each]:
			await fetcher(each, url, time, message.author.name)

async def config_fetcher(url, guild):
	filePath = "./docs/config/{}.json".format(guild)
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200:
				f = await aiofiles.open(filePath, mode='wb')
				await f.write(await resp.read())
				await f.close()
				print("[+] Saved: {}".format(filePath))

async def config_fetchEmbed(message):
	url = str(message.attachments[0].url)
	await config_fetcher(url, message.guild.id)
	
setup()
