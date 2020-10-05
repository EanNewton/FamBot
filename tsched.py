#!/usr/bin/python3

import pendulum
from sqlalchemy import and_, update, select, MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile, is_admin, incrementUsage
from constants import DIVIDER, TZ_ABBRS, ENGINE

				
def setup():
	global meta, Users, Config
	meta = MetaData()
	Users = Table(
		'schedule', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('locale', String),
		Column('guild', String),
		Column('guild_name', String),
		)
	Config = Table(
		'config', meta,
		Column('id', Integer, primary_key = True),
		Column('guild_name', String),
		Column('locale', String),
		Column('schedule', String),
		Column('quote_format', String),
		Column('lore_format', String),
		Column('url', String),
		Column('qAdd_format', String),
		)
	meta.create_all(ENGINE)
	print('[+] End Schedule Setup')
	

def helper(message):
	"""
	Main entry point from main.py
	:param message: <Discord.message object>
	:return: <lambda function> Internal function dispatch
	"""
	args = message.content.split()
	ops = {'get', 'set', 'help', 'override'}

	operator = 'get'
	if len(args) > 1 and args[1] in ops:
		operator = args[1]
	return {
		'get': lambda: getSchedule(message),
		'set': lambda: setSchedule(message),
		'help': lambda: getHelp(message),
		'override': lambda: override(message),
	}.get(operator, lambda: None)()	



def getSchedule(message):
	"""
	Generate the server schedule for a two week period.
	:param message: <Discord.message> The raw message object
	:return: <str> A formatted banner with up to 14 days of schedule + comments and links.
	"""
	incrementUsage(message.guild, 'sched')
	config = load_config(message.guild.id)

	if config:
		server_locale = config[2]
		locale = server_locale
		schedRawStr = config[3]
		url = config[6]

		#This function can be called by the bot itself from tcustom.get_command
		if not message.author.bot:
			args = message.content.split()
			if len(args) > 1: 
				#User requested specific location
				locale = TZ_ABBRS.get(args[1].lower(), args[1])
			else: 
				#Checking for saved locale in DB
				user = getUser(message.guild.id, message.author.id)
				if user:
					locale = user[2]	

		dt = pendulum.now(tz=locale)
		dtLocalName = dt.timezone.name
		now_in_server = pendulum.now(tz=server_locale)

		#Convert our raw config string from db into a workable array
		days = schedRawStr.split(';')
		dict_ = {}
		schedTime = []
		schedule = []
		hours = [day.split('=') for day in days]
		
		schedule.append(pendulum.now(tz=server_locale))
		
		for each in hours:
			if each[0] != '' and each[1] != '':
				if each[0] != ' ' and each[1] != ' ':
					dict_[int(each[0])] = each[1].split(',')
		for each in dict_.items():
			for hour in each[1]:
				if ':' in hour:
					hour = hour.split(':')
				if hour != '' and hour != ' ':
					schedTime.append(hour)
			schedule.append(pendulum.now(tz=server_locale).add(days=each[0]))

		#Needed for handling partial weeks, ie so we don't post a message with only 1 or 2 days
		scheduleDup = schedule.copy()
		#Show current server time vs current user time
		banner = '{} in {}\n'.format(dt.to_day_datetime_string(), dt.timezone_name)
		banner += '{} in {}\n'.format(now_in_server.to_day_datetime_string(), server_locale)
		banner += DIVIDER

		while(schedule[0].day_of_week != pendulum.MONDAY):
			for day in range(len(schedule)):
				schedule[day] = schedule[day].add(days=1)
		
		schedule.pop(0)
				
		#Previous / Current Week
		if now_in_server.day_of_week != pendulum.MONDAY:	
			#Get us to Monday
			while(scheduleDup[0].day_of_week != pendulum.MONDAY):
				for day in range(len(scheduleDup)):
					scheduleDup[day] = scheduleDup[day].add(days=-1)
			
			scheduleDup.pop(0)
			for day in range(len(scheduleDup)):
				if isinstance(schedTime[day], list):
					#Contains minutes
					scheduleDup[day] = scheduleDup[day].at(
						int(schedTime[day][0]), int(schedTime[day][1]))
				else:
					scheduleDup[day] = scheduleDup[day].at(int(schedTime[day]))
				
				#Convert timezone and add to message
				scheduleDup[day] = scheduleDup[day].in_tz(dtLocalName)
				if scheduleDup[day].format('DDDD') >= dt.format('DDDD'):
					if scheduleDup[day].format('DDDD') == dt.format('DDDD'):
						banner += '**{}**\n'.format(scheduleDup[day].to_day_datetime_string())
					else:
						banner += '{}\n'.format(scheduleDup[day].to_day_datetime_string())
		
		#Next Week	
		for day in range(len(schedule)):
			if isinstance(schedTime[day], list):
				#Contains minutes
				schedule[day] = schedule[day].at(
					int(schedTime[day][0]), int(schedTime[day][1]))
			else:
				schedule[day] = schedule[day].at(int(schedTime[day]))
			#Convert timezone and add to message
			schedule[day] = schedule[day].in_tz(dtLocalName)
			if schedule[day].format('DDDD') == dt.format('DDDD'):
				banner += '**{}**\n'.format(schedule[day].to_day_datetime_string())
			else:
				banner += '{}\n'.format(schedule[day].to_day_datetime_string())
				
		banner += '{}{}\n{}'.format(DIVIDER, url, DIVIDER)
		banner += 'Help pay for server costs: <{}>\n'.format('https://www.patreon.com/tangerinebot')
		banner += 'Invite the bot to your server: <{}>\n'.format('https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot')
		banner += 'Use `!schedule help` for more information.'

	else:
		banner = 'A schedule has not been setup for this server yet.\n'
		banner += 'An admin may create one with `!config`.' 
	return banner


def override(message):
	"""
	Admin command to manually change a user's saved location
	:param message: <Discord.message object> Describing which users to change to which locations
	:return: <String> Describing if the users' location was set or updated successfully
	"""
	incrementUsage(message.guild, 'sched')

	if is_admin(message.author):
		args = message.content.split()
		#Args should translate as: 1 id, 2 name, 3 locale
		
		if len(args) < 4:
			return 'Formatting is: `!schedule override [TIMEZONE] @USER` you may mention any number of users.'
		
		else:
			locale = TZ_ABBRS.get(args[2].lower(), args[2])
			success = list()

			for each in message.mentions:
				user_id = each.id
				user_name = each.name
				user = getUser(message.guild.id, int(user_id))
				
				if user:
					with ENGINE.connect() as conn:
						query = Users.update().where(Users.c.id==user_id).values(locale=locale)
						conn.execute(query)
					
					print('[+] {} UPDATED LOCALE TO {} FOR USER {}'.format(
						message.author, locale, user_name))
					success.append('Updated schedule location for {} to: {}'.format(user_name, locale))
				
				else:
					insertUser(user_id, message.guild, user_name, locale)
					print('[+] {} SETTING {}\'s SCHEDULE TO: {}'.format(
						message.author, user_name, locale))
					success.append('Set schedule location for {} to: {}'.format(user_name, locale))
			return '\n'.join(success)
			

def setSchedule(message):
	"""
	User command to set their locale
	:param message: <Discord.message object> Describing where to set location to
	:return: <String> Describing new location for user
	"""
	incrementUsage(message.guild, 'sched')
	args = message.content.split()
	config = load_config(message.guild.id)

	if config:
		server_locale = config[2]
	else:
		server_locale = 'Asia/Tokyo'

	#if no location provided default to server locale
	#if server has no locale default to Tokyo
	#if there is no server locale the schedule will not be displayed
	#however this allows users to still get their locations set
	locale = server_locale if len(args) < 3 else TZ_ABBRS.get(args[2].lower(), args[2])
	user = getUser(message.guild.id, message.author.id)
	if user:
		with ENGINE.connect() as conn:
			query = Users.update().where(
				Users.c.id == message.author.id,
				).values(locale = locale)
			conn.execute(query)
		return 'Updated your schedule location to: {}'.format(locale)
	else:
		insertUser(message.author.id, message.guild, message.author.name, locale)
		return 'Set your schedule location to: {}'.format(locale)


def insertUser(id_, guild_, name, locale):
	"""
	Internal function to set values in database for a single user
	:param id_: <Int> User ID
	:param guild_: <Discord.guild object>
	:param name: <String> Username
	:param locale: <String> New location for the user
	:return: <None>
	"""
	with ENGINE.connect() as conn:
		ins = Users.insert().values(
			id = id_,
			name = name,
			locale = locale,
			guild = guild_.id,
			guild_name = guild_.name,
		)
		conn.execute(ins)


def getUser(guild_, id_):
	"""
	Internal function to get values from database for a single user
	:param guild_: <Int> Discord guild ID, currently unused but left in so results can be limited if user is in multiple guilds
	:param id_: <Int> User ID
	:return: <List> SQLAlchemy row result from database
	"""
	with ENGINE.connect() as conn:
		select_st = select([Users]).where(
			Users.c.id == id_,)
		res = conn.execute(select_st)
		result = res.fetchone()
		if result:
			return result
	
	
def load_config(guild):
	"""
	Internal function to get Guild configuration data for schedule formatting and default locale
	:param guild: <Int> Discord guild ID
	:return: <List> SQLAlchemy row result from database
	"""
	with ENGINE.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild)
		res = conn.execute(select_st)
		result = res.fetchone()
	if result:
		return result
	return None
		

def getHelp(message):
	"""
	Get the command help file from ./docs/help
	:param message: <Discord.message object>
	:return: <String> Containing help for the user's available options or list of locations
	"""
	incrementUsage(message.guild, 'help')
	args = message.content.split()

	if len(args) < 3:
		#Get general help
		banner = fetchFile('help', 'schedule')
		if not is_admin(message.author):
			banner = banner.split('For Admins:')[0]
	else: 
		#Get list of cities or continents
		banner = fetchFile('locales', args[2].lower())

	return banner
	
		
setup()
