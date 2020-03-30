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
import discordRiddles

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
MOD_CHANNEL = os.getenv('MOD_CHANNEL')
VERSION = '3.30.2020'
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
	
	args = message.content.split()	
	profane = False
	try:
		if is_admin(message.author.roles) == False:
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
					if args[1] == 'help':
						banner = discordQuotes.helper('help', message.author)
					else:
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
						banner = discordSched.helper('help', args[2].lower(), message.author)
					else:
						banner = discordSched.helper('help', 'default', message.author)
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
		
		elif args[0] == '!riddle':
			try:
				banner = None
				if len(args) > 1:
					if args[1] == 'help':
						banner = discordRiddles.helper('help', None, message.author)

					elif args[1] == 'add':
						#id, name, text, solution
						name = ' '.join(args[2:])
						name = name.split(':')
						name = name[0]
						print("Name: " + str(name))
						solution = message.content.split('||')
						solution = solution[1].lower()
						print("Solution: " + str(solution))
						
						riddle = message.content.split(':')
						riddle = riddle[1].split('||')
						riddle = riddle[0].strip()
						print("Riddle: " + str(riddle))
						
						entity = [message.id, name, riddle, solution]
						print(entity)
						banner = entity
						banner = discordRiddles.helper('addRiddle', entity, message.author)
						
					elif args[1] == 'get':
						if len(args) > 2:
							banner = discordRiddles.helper('getRiddle', 'current', message.author)
						else:
							banner = discordRiddles.helper('getRiddle', 'new', message.author)
							
					elif args[1] == 'solve':
						riddleID = args[2]
						solution = args[3:]
						solution = ' '.join(solution)
						entity = [riddleID, solution.lower()]
						banner = discordRiddles.helper('check', entity, message.author)
					
					elif args[1] == 'score':
						banner = discordRiddles.helper('score', None, message.author)
						
					elif args[1] == 'leaderboard':
						if len(args) > 2:
							banner = discordRiddles.helper('leaderboard', None, args[2])
						else:
							banner = discordRiddles.helper('leaderboard', None, None)	
					elif args[1] == 'delete':
						if len(args) > 2 and is_admin(message.author.roles):
							banner = discordRiddles.helper('clear', args[2])
					
					elif args[1] == 'reset':
						if is_admin(message.author.roles) and args[2] == 'YES':
							banner = discordRiddles.helper('reset', None, message.author)
				if banner is not None:
					await message.channel.send(str(banner))
			except Error:
				print("Error while fetch riddle", Error)
				
		elif args[0] == '!filter':
			if is_admin(message.author.roles):
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
						banner = discordFilter.helper('add', [args[2], args[3:]])
					await message.channel.send(banner)
		elif args[0] == '!help':
			print("getting help")
			banner = discordQuotes.helper('help', message.author)
			if is_admin(message.author.roles):
				banner += discordFilter.helper('help', None)
			banner += discordSched.helper('help', 'default', message.author)+divider
			banner += discordRiddles.helper('help', None, message.author)+divider
			banner += "\n**Word of the Day**\n"+divider
			banner += "`!word` to get the word of the day. Updates once every 24 hours."
			await message.channel.send(banner)
		else:
			return


@bot.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji) == '🗨️':
		if reaction.message.author == bot.user:
			return
		else:
			exists = discordQuotes.helper('exists', reaction.message.id)
			if exists == False:
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
