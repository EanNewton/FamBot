#!/usr/bin/python3

import os
import random
import discord
import logging
import pendulum
from discord.ext import commands
from dotenv import load_dotenv
import wotd
import discordQuotes
import discordSched
import discordFilter
import discordRiddles
import discordLogger
import discordStats
from discordUtils import is_admin, is_bot, debug

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
VERSION = '5.3.2020'
bot = discord.Client()
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

@bot.event
async def on_ready():
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
	discordFilter.importBlacklists()	
	discordLogger.setup()
	discordStats.setup()
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	print("Member count: "+str(len(guildHandle.members)))
	#members = '\n - '.join([member.name for member in guildHandle.members])
	#print(f'Guild Members:\n - {members}')

@bot.event
async def on_message(message):
	if not is_bot(message.author.roles):
		#Log messages
		timestamp = pendulum.now(tz='Asia/Tokyo')
		timestamp = timestamp.to_datetime_string()
		discordLogger.corpusInsert(message, timestamp)
		if message.attachments:
			await discordLogger.fetchEmbed(message, timestamp)
		
		#Check for blacklisted words
		if discordFilter.check(message):# and is_admin(message.author) == False:
			await message.channel.send("Watch your language "+str(message.author.name)+"!")	
			return
		#Commands
		else:
			args = message.content.split()
			if args[0] == '!quote':
				banner = discordQuotes.helper(args, message.author)
			elif args[0] == '!schedule':
				banner = discordSched.helper(args, message.author)
			elif args[0] == '!word':
				banner = await wotd.getTodaysWord()
			elif args[0] == '!riddle':
				banner = discordRiddles.helper(message, message.author)
			elif args[0] == '!filter':
				if is_admin(message.author.roles):
					if len(args) > 1:
						banner = discordFilter.helper(message)
			elif args[0] == '!doip':
				banner = discordQuotes.fetchQuote("LaDoIphin")
				banner += "\n"+divider
				banner += "https://cdn.discordapp.com/attachments/486198920255635456/698328194058682368/20190305_140408.jpg"
			elif args[0] == '!help':
				banner = discordQuotes.getHelp(message.author)+'\n'+divider
				banner += discordSched.getHelp([''], message.author)+divider
				banner += discordRiddles.getHelp(message.author)+divider
				banner += discordStats.getHelp(message.author)+divider
				banner += "**Word of the Day**\n"+divider
				banner += "`!word` to get the word of the day. Updates once every 24 hours."
				if is_admin(message.author.roles):
					banner += discordFilter.getHelp()+divider
			elif args[0] == '!stats':
				banner = discordStats.helper(message)
				if banner[0]: #used because getHelp will return [None, text]
					await message.channel.send(file=discord.File(banner[0]))
				banner = banner[1]
			else:
				return
			if banner:
				await message.channel.send(banner)	

@bot.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji) == '🗨️':	 #Add a quote
		if not is_bot(reaction.message.author.roles):
			if not discordQuotes.checkExists(reaction.message.id):
				if not discordFilter.check(reaction.message):
					userName = str(reaction.message.author)
					dateTime = pendulum.now(tz='Asia/Tokyo')
					timeStamp = str(dateTime.to_day_datetime_string())
					entity = [
						reaction.message.id, 
						userName[:-5], #Trim off the discriminator tag
						reaction.message.content, 
						timeStamp
					]					
					#Prvent an @user mention from ping spamming in the quote
					for each in reaction.message.mentions:
						entity[2] = entity[2].replace('<@!'+str(each.id)+'>', each.name)
					await reaction.message.channel.send(discordQuotes.insertQuote(entity))
	
	if reaction.emoji == '❌': #Remove a quote
		users = await reaction.users().flatten()
		for user in users:
			if is_admin(user.roles):
				await reaction.message.channel.send(discordQuotes.deleteQuote(reaction.message.id))

@bot.event 
async def on_error(event, *args, **kwargs):
	with open('./err.log', 'a') as f:
		if event == 'on_message':
			print('[!] Error occurred: '+str(args[0].content))
			print('[!] Error author: '+str(args[0].author))
			f.write(f'Unhandled message: {args[0]}\n\n')
		else:
			raise
			
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)	
bot.run(TOKEN)
