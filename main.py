#!/usr/bin/python3
#TODO standardize help 
#TODO create a git commit for server join count
#TODO server invite link
#TODO update help files
#TODO move 'which command' to a function?
#TODO redo the logging to actually be useful
#TODO consolidate imports?
#TODO quotes log
#TODO fix mention supression on quotes

import logging
from random import choice, randint

import pendulum
import discord
from discord.ext import commands

import tword
import tquote
import tsched
#import tfilter
import tlog
import tstat
import tcustom
from tutil import is_admin, debug, config_create, config_helper, guildList
from tutil import config_fetchEmbed, fetchFile, incrementUsage, fetch_value, register_timer_channel
from tutil import setup as utilSetup
from speller import Speller
from constants import TOKEN, POC_TOKEN, GUILD, VERSION, EIGHTBALL, DEFAULT_DIR, help_general, DIVIDER, VERBOSE

bot = discord.Client()
spell = Speller('cmd')


@bot.event
async def on_ready():
	#global counter
	#counter = 0
	print(
		f'{bot.user} has connected to Discord!\n'
		f'Revision date: {VERSION}\n'
	)
	if VERBOSE:
		count = 0
		for each in bot.guilds:
			print(
			f'{each.name}(id: {each.id})\n'
			f'Member count: {each.member_count}'
			)
			count += each.member_count
		print(DIVIDER)
		print('Total guilds: {}'.format(len(bot.guilds)))
		print('Total members: {}'.format(count))


@bot.event
async def on_guild_join(guild):
	if VERBOSE:
		print('[+] Joined a new guild: {}'.format(guild.name))
	configFile = config_create(guild)
	banner = 'Hello {}! \n{}'.format(guild.owner.mention, fetchFile('help', 'welcome'))
	await guild.owner.send(file=discord.File('./docs/header.png'))
	await guild.owner.send(banner, file=discord.File(configFile))
	tquote.setup()
	utilSetup()



@bot.event
async def on_message(message):
	incrementUsage(message.guild, 'raw_messages')
	await tlog.logMessage(message)
	if not message.author.bot:
		'''
		#DEPRECATED
		if tfilter.check(message): #and is_admin(message.author):
			await message.channel.send('Watch your language {}!'.format(message.author.name))
			return

		else:
		'''
		args = message.content.split()
		try:
			links, banner = tcustom.get_command(message)
			if banner and links:
				await message.channel.send(links, embed=banner)
				return
			elif banner:
				await message.channel.send(embed=banner)
				return
			elif links:
				await message.channel.send(links)
				return
		except:
			pass

		# if message.content == '!create timer' and is_admin(message.author):
		# 	diff = tsched.getNextSchedTime(message)
		# 	channel = await message.guild.create_voice_channel('Next stream {}'.format(diff), position=0)
		# 	register_timer_channel(message, channel.id)
		#
		# timer_channel = message.guild.get_channel(int(fetch_value(message.guild.id, 11)))
		# try:
		# 	ra = randint(0, 100)
		# 	await timer_channel.edit(name='Next {}'.format(ra))
		# except:
		# 	pass
		#await timer_channel.edit(name='Next stream {} {}'.format(tsched.getNextSchedTime(message), counter))
		#counter += 1


		if args[0][0] != '!':
			return
		#correct minor typos
		operator = spell(args[0][1:])
		banner = [None, None]
		if VERBOSE:
			print('[-] {} by {} in {} - {}'.format(operator, message.author.name, message.channel.name, message.guild.name))

		if operator in {'quote', 'lore', 'q', 'l'}:
			banner = tquote.helper(message)
			print(type(banner))
			if type(banner) is str:
				await message.channel.send(banner)
			elif type(banner) is list:
				await message.channel.send(banner[0], file=discord.File(banner[1]))
			else:
				await message.channel.send(embed=banner)
			return

		elif operator in {'w', 'wolf', 'wolfram'}:
			banner = await tword.wolfram(message)
			#In the event there is a textual response greater than 2000 char limit
			if type(banner) is list:
				await message.channel.send(banner[0], file=discord.File(banner[1]))
			else:
				await message.channel.send(embed=banner)
			return

		elif operator in {'word', 'wotd'}:
			banner = await tword.getTodaysWord(message)
			await message.channel.send(embed=banner)
			return

		elif operator in {'poem', 'potd'}:
			banner = await tword.getTodaysPoem(message)
			await message.channel.send(embed=banner)
			return

		elif operator in {'dict', 'dictionary', 'wiki', 'wiktionary'}:
			#In order to handle long entries vs Discord's 2000 char limit,
			#wiki() will return a list and is output with for each
			banner = tword.wiki(message)
			await message.channel.send(embed=banner)
			return

		elif operator in ('translate', 'tr', 'trans'):
			banner = tword.translate(message)
			await message.channel.send(embed=banner)
			return

		elif operator in {'lmgtfy', 'google', 'g'}:
			banner = [tword.google(message, True), None]

		elif operator == 'config':
			banner = [None, config_helper(message)]

		elif operator == 'log' and is_admin(message.author):
			banner = tlog.getLog(message)
			await message.channel.send(banner[0], file=discord.File(banner[1]))
			return

		elif operator in {'schedule', 'sched', 's'}:
			banner = tsched.helper(message)
			await message.channel.send(embed=banner)
			return

		elif operator in {'yandex', 'image', 'tineye', 'reverse'}:
			banner = [tword.yandex(message), None]

		#elif operator == 'filter':
		#	banner = [tfilter.helper(message), None]

		elif operator == 'doip' and int(message.guild.id) == 453859595262361611:
			incrementUsage(message.guild, 'doip')
			await message.channel.send(tquote.getQuoteRaw(message.guild.id, tquote.Quotes, "LaDoIphin"), file=discord.File('{}/docs/doip.jpg'.format(DEFAULT_DIR)))

		elif operator in {'gif', 'react', 'meme'}:
			if len(args) > 1 and args[1] == 'add':
				await tquote.fetchReact(message)
			else:
				banner = tquote.getReact(message)

		elif operator == 'stats':
			image, banner = tstat.helper(message)
			await message.channel.send(file=image, embed=banner)

		elif operator in {'8ball', '88ball', 'ball', '8', 'eightball', 'eight'}:
			incrementUsage(message.guild, 'eight')
			await message.channel.send(choice(EIGHTBALL))
			return

		elif operator == 'help':
			incrementUsage(message.guild, 'help')
			help_ = fetchFile('help', 'general')
			if not is_admin(message.author):
				help_ = help_.split('For Admins:')[0]

			banner = discord.Embed(title='General Help', description=help_)
			banner.add_field(name='Help support this bot!', value='All donations go to development and server costs.', inline=False)
			banner.add_field(name='PayPal', value=help_general['paypal'])
			banner.add_field(name='Patreon', value=help_general['patreon'])
			banner.add_field(name='More Information', value='This bot is open source, find it at: {}'.format(help_general['github']))
			banner.add_field(name='Invite the bot to your server.', value=help_general['invite'], inline=False)

			await message.channel.send(embed=banner)
			return

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
			#if not tfilter.check(message) or is_admin(payload.member):
			banner = tquote.insertQuote(message, None, payload.member.name)
			await message.channel.send(embed=banner)
	
	#Remove a quote
	#emoji is :x:
	if str(payload.emoji) == '❌' and is_admin(payload.member): 
		banner = tquote.deleteQuote(message.guild.id, message.id)
		await message.channel.send(banner)
		await message.channel.send(tcustom.delete_command(message))

	#Add a custom guild command
	#emoji is :gear:
	if str(payload.emoji) == '⚙️' and is_admin(payload.member): 
		await message.channel.send(embed=tcustom.insert_command(message))



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
