#!/usr/bin/python3
#TODO dictionary.com / thesaurus lookup

from os import getenv
import logging
from random import choice

import pendulum
import discord
from discord.ext import commands
from dotenv import load_dotenv

import tword
import tquote
import tsched
import tfilter
import tlog
import tstat
from tutil import is_admin, is_bot, debug, config_create, config_reset
from tutil import config_fetchEmbed, fetchFile
from speller import Speller

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
GUILD = getenv('DISCORD_GUILD')
VERSION = '6.1.2020'
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 
bot = discord.Client()
spell = Speller('cmd')


@bot.event
async def on_ready():
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	print('Member count: {}'.format(len(guildHandle.members)))
	#members = '\n - '.join([member.name for member in guildHandle.members])
	#print(f'Guild Members:\n - {members}')


@bot.event
async def on_guild_join(guild):
	banner = 'Hello {}! \n{}'.format(guild.owner.mention, fetchFile('help', 'welcome'))
	await guild.system_channel.send(banner, file=discord.File('./docs/header.png'))


@bot.event
async def on_message(message):
	#if not is_bot(message.author):
	if not message.author.bot:
		#Log messages
		timestamp = pendulum.now(tz='Asia/Tokyo').to_datetime_string()
		tlog.corpusInsert(message, timestamp)
		if message.attachments:
			await tlog.fetchEmbed(message, timestamp)
			#Loading in server config file
			if is_admin(message.author) and message.attachments[0].filename == '{}.json'.format(message.guild.id):
					await config_fetchEmbed(message)
					tfilter.importCustom(message.guild.id)
			
		if tfilter.check(message): #and is_admin(message.author):
			await message.channel.send('Watch your language {}!'.format(message.author.name))
			return
		else:
			args = message.content.split()
			if not args[0][0] == '!':
				return
			#correct minor typos
			args[0] = '!{}'.format(spell(args[0][1:]))
			
			if args[0] in {'!quote', '!lore', '!q', '!l'}:
				banner = tquote.helper(message)
				
			elif args[0] in {'!dict', '!dictionary'}:
				#In order to handle long entries vs Discord's 2000 char limit,
				#wiki() will return a list and is output with for each
				banner = tword.wiki(' '.join(args[1:]))
				for each in banner:
					await message.channel.send(each)
				return
				
			elif args[0] in {'!lmgtfy', '!google', '!g'}:
				banner = 'https://google.com/search?q={}'.format('+'.join(args[1:]))
			
			elif args[0] == '!config' and is_admin(message.author):
				if len(args) > 1 and args[1] == 'reset':
					banner = config_reset(message.guild)
				else:
					banner = config_create(message.guild)
				await message.channel.send(file=discord.File(banner))
				return
			
			elif args[0] in {'!schedule', '!sched', '!s'}:
				banner = tsched.helper(message)
			
			elif args[0] == '!word':
				banner = await tword.getTodaysWord()
			
			elif args[0] == '!filter':
				if len(args) > 1 and is_admin(message.author):
					banner = tfilter.helper(message)
			
			elif args[0] == '!doip':
				banner = tquote.getQuote(None, message.guild.id, "LaDoIphin")
				await message.channel.send(banner, file=discord.File('./docs/doip.jpg'))
				return
					
			elif args[0] == '!stats':
				banner = tstat.helper(message)
				if banner[0]: #used because tstat.getHelp will return [None, text]
					await message.channel.send(banner[1], file=discord.File(banner[0]))
					return
				banner = banner[1]
			
			elif args[0] in {'!8ball', '!8', '!eightball', '!eight'}:
				banner = choice([
					'It is certain.', 'It is decidedly so.', 'Without a doubt.',
					'Yes -- definitely.', 'You may rely on it.', 'As I see it, yes.',
					'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.',
					'Reply hazy, try again.', 'Ask again later.', 
					'Better not tell you now.', 'Cannot predict now.',
					'Concentrate and ask again.', 'Don\'t count on it.', 
					'My reply is no.', 'My sources say no.', 'Outlook not so good',
					'Very doubtful.'
					])
				
			elif args[0] == '!help':
				banner = '`!quote help`\n`!lore help`\n`!schedule help`\n'
				banner += '`!stats help`\n'
				banner += '`!word` to get the word of the day. Updates once every 24 hours.\n'
				banner += divider
				if is_admin(message.author):
					banner += '**Use `!config` to change server settings.**\n'
				banner += 'Donation link: <{}>\n'.format('https://www.patreon.com/tangerinebot')
				banner += 'Invite link: <{}>\n'.format('https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot')
				banner += 'This bot is open source, find the code at: <{}>'.format('https://github.com/EanNewton/FamBot')
				
			if banner:
				await message.channel.send(banner)	


@bot.event
async def on_raw_reaction_add(payload): 
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	
	#Add a quote
	if str(payload.emoji) == '🗨️' and not message.author.bot:
		if not tquote.checkExists(message.guild.id, message.id):
			if not tfilter.check(message) or is_admin(payload.member):
				await message.channel.send(tquote.insertQuote(None, message))
	
	#Remove a quote
	if str(payload.emoji) == '❌'and is_admin(payload.member): 
		await message.channel.send(tquote.deleteQuote(message.guild.id, message.id))


@bot.event 
async def on_error(event, *args, **kwargs):
	with open('./log/err.log', 'a') as f:
		if event == 'on_message':
			timestamp = pendulum.now(tz='America/Phoenix').to_datetime_string()
			print(timestamp)
			print('[!] Error in: {}; {}'.format(args[0].channel.name, args[0].guild.name))
			print('[!] Error content: {}'.format(args[0].content))
			print('[!] Error author: {}'.format(args[0].author))
			f.write(f'{timestamp}\nUnhandled message:\n{args[0]}\n\n')
		else:
			raise
			
			
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='./log/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)	

bot.run(TOKEN)
