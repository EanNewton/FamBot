#!/usr/bin/python3

import os
import random
import discord
import pendulum
from discord.ext import commands
from dotenv import load_dotenv
import wotd
import discordQuotes
import discordSched
import discordFilter

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
MOD_CHANNEL = os.getenv('MOD_CHANNEL')
VERSION = '3.27.2020'
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

bot = discord.Client()
adminRoles = {'admin', 'mod', 'discord mod'}
blacklistLow = discordFilter.getBlacklistLow()
blacklistStrict = discordFilter.getBlacklistStrict()

divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

def is_admin(author):
	for roles in author:
		if str(roles).lower() in adminRoles:
			return True
	return False

@bot.event
async def on_ready():
	global guildHandle
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
			
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	#members = '\n - '.join([member.name for member in guildHandle.members])
	#print(f'Guild Members:\n - {members}')

@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	
	admin = is_admin(message.author.roles)
	args = message.content.split()	
	profane = False
	try:
		if admin:
			if discordFilter.helper('get', message.channel.id) == "Filter level: 2":
				for word in args:
					if word in blacklistStrict or word in blacklistLow:
						profane = True
						await message.channel.send("Watch your language!")
			elif discordFilter.helper('get', message.channel.id) == "Filter level: 1":
				for word in args:
					if word in blacklistLow:
						profane = True
						await message.channel.send("Watch your language!")
	except Error:
		print("Error on profanity filter: ", Error)
	if not profane:
		if args[0] == '!quote':
			try:
				if len(args) > 1:
					toFetch = message.content[7:]
					print('Pulling quote from: '+str(toFetch))
					banner = discordQuotes.fetchQuote(toFetch)
				else:
					banner = discordQuotes.fetchQuote(-1)
				await message.channel.send(str(banner))
			except Error:
				print("Error while fetch rand", Error)

		elif args[0] == '!schedule':
			if len(args) > 1:
				if args[1] == 'help':
					if len(args) > 2:					
						banner = discordSched.helper('help', args[2].lower(), None)
					else:
						banner = discordSched.helper('help', 'default', None)
				elif args[1] == 'set':
					banner = discordSched.helper('set', args[2], message.author)
				elif args[1] == 'override':
					banner = discordSched.helper('override', args[2:], message.author)
				else:
					banner = discordSched.helper('get', args[1:], message.author.id)
			else:
				banner = discordSched.helper('get', None, message.author.id)
			print(banner)
			await message.channel.send(banner)	
				
		elif args[0] == '!word':
			banner = wotd.getTodaysWord(True)
			await message.channel.send(str(banner))
			
		elif args[0] == '!filter':
			if admin:
				if len(args) > 1:
					if args[1] == 'set':
						banner = discordFilter.helper('set', [message.channel.id, args[2]])
					elif args[1] == 'get':
						banner = discordFilter.helper('get', message.channel.id)
					elif args[1] == 'clearall':
						banner = discordFilter.helper('clearAll', None)
					elif args[1] == 'clear':
						banner = discordFilter.helper('clear', message.channel.id)
					elif args[1] == 'help':
						banner = discordFilter.helper('help', None)
					elif args[1] == 'add':
						banner = discordFilter.helper('add', [args[2], args[3]])
					await message.channel.send(banner)
		elif args[0] == '!help':
			#print("getting help")
			banner = discordQuotes.helper('help', admin)
			#print(banner)
			banner += discordFilter.helper('help', admin)
			#print(banner)
			banner += discordSched.helper('help', 'default', admin)+divider
			#print(banner)
			banner += "\n**Word of the Day**\n"+divider
			banner += "`!word` to get the word of the day. Updates once every 24 hours."
			#print(banner)
			await message.channel.send(banner)
		else:
			return


@bot.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji) == '🗨️':
		if reaction.message.author == bot.user:
			return
		else:
			args = reaction.message.content.split()	
			profane = False
			userName = str(reaction.message.author)
			dateTime = pendulum.now(tz='Asia/Tokyo')
			timeStamp = str(dateTime.to_day_datetime_string())
			
			entity = [reaction.message.id, userName[:-5], reaction.message.content, str(timeStamp)]
			if discordFilter.helper('get', reaction.message.channel.id) == "Filter level: 2":
				for word in args:
					if word in blacklistStrict:
						profane = True
			if discordFilter.helper('get', reaction.message.channel.id) == "Filter level: 1":
				for word in args:
					if word in blacklistLow:
						profane = True
			users = await reaction.users().flatten()
			for user in users:
				if is_admin(user.roles):
					profane = False
			if not profane: 
				discordQuotes.helper('add', entity)
				banner = 'Adding: "' +str(entity[2])+'" by '+str(entity[1])+' on '+str(timeStamp)
				await reaction.message.channel.send(banner)
	
	if reaction.emoji == '❌':
		users = await reaction.users().flatten()
		for user in users:
			if is_admin(user.roles):
				banner = discordQuotes.helper('clear', reaction.message.id)
				await reaction.message.channel.send(banner)

@bot.event 
async def on_error(event, *args, **kwargs):
	with open('./err.log', 'a') as f:
		if event == 'on_message':
			print('Error occurred: '+args[0].content)
			print('Error author: '+str(args[0].author))
			f.write(f'Unhandled message: {args[0]}\n\n')
		else:
			raise
	
bot.run(TOKEN)
