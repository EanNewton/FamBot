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
from discordUtils import is_admin, is_bot

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
#MOD_CHANNEL = os.getenv('MOD_CHANNEL')
VERSION = '4.28.2020'

bot = discord.Client()

divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

@bot.event
async def on_ready():
	global guildHandle
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
	discordFilter.importBlacklists()	
	discordLogger.setup()
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	members = '\n - '.join([member.name for member in guildHandle.members])
	print("Member count: "+str(len(guildHandle.members)))
	print(f'Guild Members:\n - {members}')

@bot.event
async def on_message(message):
	if is_bot(message.author.roles):
		return
	else:
		#Log messages
		discordLogger.corpusInsert(message)
		if message.attachments:
			timestamp = pendulum.now(tz='Asia/Tokyo')
			timestamp = timestamp.to_datetime_string()
			await discordLogger.fetchEmbed(message, timestamp)
		#Check for blacklisted words
		if discordFilter.check(message) and is_admin(message.author) == False:
			await message.channel.send("Watch your language "+str(message.author.name)+"!")	
			return
		else:
			#Commands
			args = message.content.split()
			if args[0] == '!quote':
				banner = discordQuotes.helper(args, message.author)
				await message.channel.send(banner)
			elif args[0] == '!schedule':
				banner = discordSched.helper(args, message.author)
				await message.channel.send(banner)	
			elif args[0] == '!word':
				banner = await wotd.getTodaysWord(True)
				await message.channel.send(banner)
			elif args[0] == '.riddle':
				banner = discordRiddles.helper(message, message.author)
				await message.channel.send(banner)	
			elif args[0] == '!filter':
				if is_admin(message.author.roles):
					if len(args) > 1:
						await message.channel.send(discordFilter.helper(message))
			elif args[0] == '!doip':
				banner = discordQuotes.fetchQuote("LaDoIphin")
				banner += "\n"+divider
				banner += "https://cdn.discordapp.com/attachments/486198920255635456/698328194058682368/20190305_140408.jpg"
				await message.channel.send(banner)
			elif args[0] == '!help':
				print("[-] Getting help")
				banner = discordQuotes.get_help(message.author)+'\n'+divider
				if is_admin(message.author.roles):
					banner += discordFilter.get_help()+divider
				banner += discordSched.get_help([''], message.author)+divider
				banner += discordRiddles.get_help(message.author)+divider
				banner += "**Word of the Day**\n"+divider
				banner += "`!word` to get the word of the day. Updates once every 24 hours."
				await message.channel.send(banner)
			else:
				return

@bot.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji) == '🗨️':	 #Add a quote
		if is_bot(reaction.message.author.roles) == False:
			if discordQuotes.check_if_exists(reaction.message.id) == False:
				if discordFilter.check(reaction.message):
					return
				else:
					userName = str(reaction.message.author)
					dateTime = pendulum.now(tz='Asia/Tokyo')
					timeStamp = str(dateTime.to_day_datetime_string())
					entity = [reaction.message.id, userName[:-5], reaction.message.content, str(timeStamp)]
					
					#Prvent an @user mention from ping spamming in the quote
					for each in reaction.message.mentions:
						entity[2] = entity[2].replace('<@!'+str(each.id)+'>', each.name)
				
					discordQuotes.sql_insert_quote(entity)
					banner = 'Adding: "' +str(entity[2])+'" by '+str(entity[1])+' on '+str(timeStamp)
					await reaction.message.channel.send(banner)
	
	if reaction.emoji == '❌': #Remove a quote
		users = await reaction.users().flatten()
		for user in users:
			if is_admin(user.roles):
				await reaction.message.channel.send(discordQuotes.delete_quote(str(reaction.message.id)))

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
