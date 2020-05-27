#!/usr/bin/python3

from os import getenv
import logging

import pendulum
import discord
from discord.ext import commands
from dotenv import load_dotenv

import tword
import tquote
import tsched
#import tfilter
import tlog
import tstat
from tutil import is_admin, is_bot, debug, config_create, config_reset
from tutil import config_fetchEmbed

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
GUILD = getenv('DISCORD_GUILD')
VERSION = '5.26.2020'
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 
bot = discord.Client()


@bot.event
async def on_ready():
	guildHandle = discord.utils.get(bot.guilds, name=GUILD)
	print(
	f'{bot.user} has connected to Discord!\n'
	f'{guildHandle.name}(id: {guildHandle.id})\n'
	f'Revision date: {VERSION}\n'
	)
	print('Member count: {}'.format(len(guildHandle.members)))
	#tfilter.importBlacklists()	
	#members = '\n - '.join([member.name for member in guildHandle.members])
	#print(f'Guild Members:\n - {members}')


@bot.event
async def on_guild_join(guild):
	banner = 'Hello {}! To get started make sure you and your admins have a role named \
	"mod" or "admin" and then use `!config` and `!help`.'.format(guild.owner.mention)
	await guild.system_channel.send(banner)


@bot.event
async def on_message(message):
	if not is_bot(message.author.roles):
		#Log messages
		timestamp = pendulum.now(tz='Asia/Tokyo').to_datetime_string()
		tlog.corpusInsert(message, timestamp)
		if message.attachments:
			await tlog.fetchEmbed(message, timestamp)
			#Loading in server config file
			if is_admin(message.author.roles):
				if message.attachments[0].filename == '{}.json'.format(message.guild.id):
					await config_fetchEmbed(message)
			
		
		#Check for blacklisted words
		#if tfilter.check(message):# and is_admin(message.author) == False:
		#	await message.channel.send("Watch your language "+str(message.author.name)+"!")	
		#	return
		#Commands
		if True: #DEBUGGING line, remove if filter uncommented
			args = message.content.split()
			if args[0] == '!quote' or args[0] == '!lore':
				banner = tquote.helper(message)
			
			elif args[0] == '!config':
				if is_admin(message.author.roles):
					if len(args) > 1 and args[1] == 'reset':
						banner = config_reset(message.guild)
					else:
						banner = config_create(message.guild)
					await message.channel.send(banner[0], file=discord.File(banner[1]))
					return
			
			elif args[0] == '!schedule' or args[0] == '!sched':
				banner = tsched.helper(message)
			
			elif args[0] == '!word':
				banner = await wotd.getTodaysWord()
			
			#elif args[0] == '!filter':
			#	if is_admin(message.author.roles):
			#		if len(args) > 1:
			#			banner = tfilter.helper(message)
			
			elif args[0] == '!doip':
				banner = tquote.getQuote(None, message.guild.id, "LaDoIphin")
				await message.channel.send(banner, file=discord.File('./docs/doip.jpg'))
				return
			
			elif args[0] == '!help':
				banner = tquote.getHelp(message.author)+'\n'+divider
				banner += tsched.getHelp([''], message.author)+divider
				banner += tstat.getHelp()[1]				
				banner += '**Word of the Day**\n'
				banner += '`!word` to get the word of the day. Updates once every 24 hours.\n'
				if is_admin(message.author.roles):
				#	banner += tfilter.getHelp()+divider
					banner += divider
					banner += '**Use `!config` to change server settings.**'
			
			elif args[0] == '!stats':
				banner = tstat.helper(message)
				if banner[0]: #used because getHelp will return [None, text]
					await message.channel.send(file=discord.File(banner[0]))
				banner = banner[1]
			
			else:
				return
			if banner:
				await message.channel.send(banner)	


@bot.event
async def on_raw_reaction_add(payload):
	member = payload.member 
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	
	#Add a quote
	if str(payload.emoji) == '🗨️' and not is_bot(message.author.roles):
		if not tquote.checkExists(message.guild.id, message.id):
			await message.channel.send(tquote.insertQuote(None, message))
	
	#Remove a quote
	if str(payload.emoji) == '❌'and is_admin(member.roles): 
		await message.channel.send(tquote.deleteQuote(message.guild.id, message.id))


@bot.event 
async def on_error(event, *args, **kwargs):
	with open('./log/err.log', 'a') as f:
		if event == 'on_message':
			print('[!] Error occurred: {}'.format(args[0].content))
			print('[!] Error channel: {}'.format(args[0].channel.name))
			print('[!] Error author: {}'.format(args[0].author))
			print('[!] Error guild: {}'.format(args[0].guild.name))
			f.write(f'Unhandled message: {args[0]}\n\n')
		else:
			raise
			
			
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='./log/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)	

bot.run(TOKEN)
