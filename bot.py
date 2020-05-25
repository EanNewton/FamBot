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
import discordLogger
import discordStats
from discordUtils import is_admin, is_bot, debug, create_config, load_config, reset_config
from pathlib import Path

Path("./log/audio").mkdir(parents=True, exist_ok=True)
Path("./log/docs").mkdir(parents=True, exist_ok=True)
Path("./log/images").mkdir(parents=True, exist_ok=True)
Path("./log/video").mkdir(parents=True, exist_ok=True)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
VERSION = '5.25.2020'
bot = discord.Client()
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 


@bot.event
async def on_ready():
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	print("Member count: {}".format(len(guildHandle.members)))
	discordFilter.importBlacklists()	
	#members = '\n - '.join([member.name for member in guildHandle.members])
	#print(f'Guild Members:\n - {members}')

@bot.event
async def on_guild_join(guild):
	banner = 'Hello {}! To get started make sure you and your admins have a role named "mod" or "admin" and then use `!config` and `!help`.'.format(guild.owner.mention)
	await guild.system_channel.send(banner)

@bot.event
async def on_message(message):
	if not is_bot(message.author.roles):
		#Log messages
		timestamp = pendulum.now(tz='Asia/Tokyo')
		timestamp = timestamp.to_datetime_string()
		discordLogger.corpusInsert(message, timestamp)
		if message.attachments:
			await discordLogger.fetchEmbed(message, timestamp)
			#Loading in server config file
			if is_admin(message.author.roles):
				if message.attachments[0].filename == '{}.json'.format(message.guild.id):
					await discordLogger.config_fetchEmbed(message)
					load_config(message.guild.id)
			
		
		#Check for blacklisted words
		#if discordFilter.check(message):# and is_admin(message.author) == False:
		#	await message.channel.send("Watch your language "+str(message.author.name)+"!")	
		#	return
		#Commands
		if True:
			args = message.content.split()
			if args[0] == '!quote' or args[0] == '!lore':
				banner = discordQuotes.helper(message)
			elif args[0] == '!config':
				if is_admin(message.author.roles):
					if len(args) > 1:
						if args[1] == 'reset':
							banner = reset_config(message.guild)
					else:
						banner = create_config(message.guild)
					await message.channel.send(banner[0], file=discord.File(banner[1]))
					return
			elif args[0] == '!schedule' or args[0] == '!sched':
				banner = discordSched.helper(message)
			elif args[0] == '!word':
				banner = await wotd.getTodaysWord()
			elif args[0] == '!filter':
				if is_admin(message.author.roles):
					if len(args) > 1:
						banner = discordFilter.helper(message)
			elif args[0] == '!doip':
				banner = discordQuotes.getQuote(None, message.guild.id, "LaDoIphin")
				banner += "\n"+divider
				await message.channel.send(banner, file=discord.File('./docs/doip.jpg'))
				return
			elif args[0] == '!help':
				banner = discordQuotes.getHelp(message.author)+'\n'+divider
				banner += discordSched.getHelp([''], message.author)+divider
				banner += discordStats.getHelp()[1]
				#await message.channel.send(banner)	
				
				banner += "**Word of the Day**\n"+divider
				banner += "`!word` to get the word of the day. Updates once every 24 hours.\n"
				if is_admin(message.author.roles):
				#	banner += discordFilter.getHelp()+divider
					banner += divider
					banner += '**Use `!config` to change server settings.**'
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
async def on_raw_reaction_add(payload):
	member = payload.member #The user adding the reaction
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	#Add a quote
	if str(payload.emoji) == '🗨️' and not is_bot(message.author.roles):
		if discordQuotes.checkExists(message.guild.id, message.id):
			await message.channel.send(discordQuotes.insertQuote(None, message))
	
	#Remove a quote
	if str(payload.emoji) == '❌'and is_admin(member.roles): 
		await message.channel.send(discordQuotes.deleteQuote(message.guild.id, message.id))

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
