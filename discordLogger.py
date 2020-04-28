#!/usr/bin/python3

import sqlalchemy
import pendulum
import logging
import asyncio
import aiohttp
import aiofiles

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String 
 	
extSet_img = {
	'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'
	}   
extSet_audio = {
	'3gp', 'aa', 'aac', 'aax', 'act', 'aiff', 'alac', 'amr', 'ape',
	'au', 'awb', 'dct', 'dss', 'dvf', 'flac', 'gsm', 'iklax', 'ivs',
	'm4a', 'm4b', 'm4p', 'mmf', 'mp3', 'mpc', 'msv', 'nmf', 'nsf',
	'ogg', 'oga', 'mogg', 'opus', 'ra', 'rm', 'raw', 'rf64', 'sln',
	'tta', 'voc', 'vox', 'wav', 'wma', 'wv', 'webm', '8svx', 'cda'
	}
extSet_video = {
	'webm', 'mkv', 'flv', 'vob', 'ogv', 'ogg', 'drc', 'gifv', 'mng',
	'avi', 'mts', 'm2ts', 'ts', 'mov', 'qt', 'wmv', 'yuv', 'rm', 
	'rmvb', 'asf', 'amv', 'mp4', 'm4p', 'm4v', 'mpg', 'mp2', 'mpeg',
	'mpe', 'mpv', 'm4v', 'svi', '3gp', '3g2', 'mxf', 'roq', 'nsv',
	'f4v', 'f4p', 'f4a', 'f4b'
	}
extSet_documents = {
	'0', '1st', '600', '602', 'abw', 'acl', ' afp', 'ami', 'ans', 'asc',
	'aww', 'ccf' 'csv', 'cwk', 'dbk', 'dita', 'doc', 'docm', 'docx', 'dot'
	'dotx', 'dwd', 'egt', 'epub', 'ezw', 'fdx', 'ftm', 'ftx', 'gdoc', 
	'html', 'hwp', 'hwpml', 'log', 'lwp', 'mbp', 'md', 'me', 'mcw', 'mobi',
	'nb', 'nbp', 'neis', 'odm', 'odoc', 'odt', 'osheet', 'ott', 'omm',
	'pages', 'pap', 'pdax', 'pdf', 'quox', 'rtf', 'rpt', 'sdw', 'se',
	'stw', 'sxw', 'tex', 'info', 'troff', 'txt', 'uof', 'uoml', 'via',
	'wpd', 'wps', 'wpt', 'wrd', 'wrf', 'wri', 'xhtml', 'xht', 'xml', 'xps'
	}

def setup():
	engine = create_engine('sqlite:///./log/logger.db', echo = False)
	meta = MetaData()
	corpus = Table(
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
		Column('reactions', String)
		)
	meta.create_all(engine)
	print('[+] End Corpus.db Setup')

	
def corpusInsert(message):
	mChanMentions = ''
	mAttach = ''
	mMentions = ''
	mEmbeds = ''
	mRoleMentions = ''
	dateTime = pendulum.now(tz='Asia/Tokyo')
	timeStamp = str(dateTime.to_day_datetime_string())
	
	engine = create_engine('sqlite:///./log/logger.db', echo = False)
	meta = MetaData()
	corpus = Table(
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
		Column('reactions', String)
		)

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
	
	ins = corpus.insert().values(
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
		reactions = "none"
		)
	conn = engine.connect()
	result = conn.execute(ins)

async def fetcher(filetype, url, time, author):
	async with aiohttp.ClientSession() as session:
		filePath = "./log/"+filetype+"/"+author+"_"+time+"_"+url.split('/')[-1]
		async with session.get(url) as resp:
			if resp.status == 200:
				f = await aiofiles.open(filePath, mode='wb')
				await f.write(await resp.read())
				await f.close()
				print("[+] Saved "+filetype+": "+str(filePath))

async def fetchEmbed(message, time):
	url = str(message.attachments[0].url)
	ext = str(url.split('.')[-1].lower())
	
	if ext in extSet_img:
		await fetcher("images", url, str(time), str(message.author.name))
	elif ext in extSet_audio:
		await fetcher("audio", url, str(time), str(message.author.name))
	elif ext in extSet_video:
		await fetcher("video", url, str(time), str(message.author.name))
	elif ext in extSet_documents:
		await fetcher("docs", url, str(time), str(message.author.name))
		
