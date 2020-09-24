#!/usr/bin/python3
#TODO standardize help 
#TODO create a git commit for server join count
#TODO server invite link
#TODO update help files
#TODO move 'which command' to a function?
#TODO redo the logging to actually be useful
#TODO consolidate imports?

import logging
from random import choice

import pendulum
import discord
from discord.ext import commands

import tword
import tquote
import tsched
import tfilter
import tlog
import tstat
import tcustom
from tutil import is_admin, debug, config_create, config_helper
from tutil import config_fetchEmbed, fetchFile, incrementUsage
from speller import Speller
from constants import TOKEN, POC_TOKEN, GUILD, VERSION, EIGHTBALL

bot = discord.Client()
spell = Speller('cmd')

@bot.event
async def on_ready():
	print(bot)
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
	print('[+] Joined a new guild: {}'.format(guild.name))
	configFile = config_create(guild)
	banner = 'Hello {}! \n{}'.format(guild.owner.mention, fetchFile('help', 'welcome'))
	await guild.owner.send(file=discord.File('./docs/header.png'))
	await guild.owner.send(banner, file=discord.File(configFile))


@bot.event
async def on_message(message):
	if not message.author.bot:
		incrementUsage(message.guild, 'raw_messages')
		await tlog.logMessage(message)
			
		if tfilter.check(message): #and is_admin(message.author):
			await message.channel.send('Watch your language {}!'.format(message.author.name))
			return

		else:
			args = message.content.split()
			banner = tcustom.get_command(message)
			if banner:
				await message.channel.send(banner)
				return

			if not args[0][0] == '!':
				return
			#correct minor typos
			operator = spell(args[0][1:])
			banner = [None, None]
			
			if operator in {'quote', 'lore', 'q', 'l'}:
				banner = [tquote.helper(message), None]

			elif operator in {'delete', 'remove'}:
				banner = [tcustom.delete_command(message), None]

			elif operator in {'w', 'wolf', 'wolfram'}:
				banner = await tword.wolfram(message)
				#In the event there is a textual response greater than 2000 char limit
				if type(banner[0]) is list():
					for each in banner[0]:
						await message.channel.send(each)
					return
			
			elif operator in {'word', 'wotd'}:
				banner = [await tword.getTodaysWord(message), None]

			elif operator in {'dict', 'dictionary'}:
				#In order to handle long entries vs Discord's 2000 char limit,
				#wiki() will return a list and is output with for each
				banner = tword.wiki(message)
				for each in banner:
					await message.channel.send(each)
				return

			elif operator in ('translate', 'tr', 'trans'):
				banner = [tword.translate(message), None]
				for each in banner:
					await message.channel.send(each)
				return

			elif operator in {'lmgtfy', 'google', 'g'}:
				banner = [tword.google(message, True), None]
				
			elif operator == 'config':
				banner = [None, config_helper(message)]
			
			elif operator in {'schedule', 'sched', 's'}:
				banner = [tsched.helper(message), None]
			
			elif operator == 'filter':
				banner = [tfilter.helper(message), None]
			
			elif operator == 'doip' and message.guild.id == '453859595262361611':
				incrementUsage(message.guild, 'doip')
				banner = [tquote.getQuote(None, message.guild.id, "LaDoIphin"), './docs/doip.jpg']
				
			elif operator in {'gif', 'react', 'meme'}:
				if len(args) > 1 and args[1] == 'add':
					await tquote.fetchReact(message)
				else:
					banner = tquote.getReact(message)
					
			elif operator == 'stats':
				banner = tstat.helper(message)
			
			elif operator in {'8ball', '88ball', 'ball', '8', 'eightball', 'eight'}:
				incrementUsage(message.guild, 'eight')
				banner = [choice(EIGHTBALL), None]
				
			elif operator == 'help':
				incrementUsage(message.guild, 'help')
				banner = fetchFile('help', 'general')
				if not is_admin(message.author):
					banner = banner.split('For Admins:')[0]
				banner = [banner, None]

			if banner[1]:
				await message.channel.send(banner[0], file=discord.File(banner[1]))	
			else:
				await message.channel.send(banner[0])


@bot.event
async def on_raw_reaction_add(payload): 
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	
	#Add a quote
	#emoji is :speech_left:
	if str(payload.emoji) == '🗨️' and not message.author.bot:
		if not tquote.checkExists(message.guild.id, message.id):
			if not tfilter.check(message) or is_admin(payload.member):
				await message.channel.send(tquote.insertQuote(message, None))
	
	#Remove a quote
	#emoji is :x:
	if str(payload.emoji) == '❌' and is_admin(payload.member): 
		await message.channel.send(tquote.deleteQuote(message.guild.id, message.id))

	#Add a custom guild command
	#emoji is :gear:
	if str(payload.emoji) == '⚙️' and is_admin(payload.member): 
		await message.channel.send(tcustom.insert_command(message))



@bot.event 
async def on_error(event, *args, **kwargs):
	#For errors with the bot itself
	with open('./log/err.log', 'a') as f:
		if event == 'on_message':
			timestamp = pendulum.now(tz='America/Phoenix').to_datetime_string()
			location = '[!] Error in: {}; {}'.format(args[0].channel.name, args[0].guild.name)
			content = '[!] Error content: {}'.format(args[0].content)
			author = '[!] Error author: {}'.format(args[0].author)

			f.write('{}\nUnhandled message:{}\n{}\n{}\n{}\n\n'.format(
				timestamp,
				args[0],
				location,
				author,
				content,
				))
		else:
			return
			
#For errors with the discord client or API			
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='./log/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)	

bot.run(POC_TOKEN)
