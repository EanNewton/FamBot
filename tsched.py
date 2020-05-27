#!/usr/bin/python3

import pendulum
from sqlalchemy import create_engine, and_, update, select, MetaData, Table, Column, Integer, String 

from tutil import debug, fetchFile, is_admin

tzAbbrs = {} 
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

				
def setup():
	global engine, meta, Users, Config
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
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
	meta.create_all(engine)
	with open('./docs/locales/abbr.txt', 'r') as f:
		for line in f:
			(key, val) = line.split(',')
			val = val.strip('\n')
			tzAbbrs[key] = val
	print('[+] End Schedule Setup')
	

def helper(message):
	args = message.content.split()
	ops = {'get', 'set', 'help', 'override', 'config'}
	operator = 'get'
	if len(args) > 1 and args[1] in ops:
		operator = args[1]
	return {
		'get': lambda: getSchedule(message),
		'set': lambda: setSchedule(message),
		'help': lambda: getHelp(args, message.author),
		'override': lambda: override(message),
	}.get(operator, lambda: None)()	


def getSchedule(message):
#yes, it is ugly, but it works
#if you can get a cleaner version working please submit a github request
	config = load_config(message.guild.id)
	if config:
		server_locale = config[2]
		locale = server_locale
		schedRawStr = config[3]
		url = config[6]
			
		args = message.content.split()
		if len(args) > 1: #User requested specific location
			locale = tzAbbrs.get(args[1].lower(), args[1])
		else: #Checking for saved locale in DB
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
		banner += divider

		while(schedule[0].day_of_week != pendulum.MONDAY):
			for day in range(len(schedule)):
				schedule[day] = schedule[day].add(days=1)
					
		#Previous / Current Week
		if now_in_server.day_of_week != pendulum.MONDAY:	
			#Get us to Monday
			while(scheduleDup[0].day_of_week != pendulum.MONDAY):
				for day in range(len(scheduleDup)):
					scheduleDup[day] = scheduleDup[day].add(days=-1)
			
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
				
		banner += '{}{}\n{}'.format(divider, url, divider)
		banner += 'You can set your schedule location with `!schedule set LOCATION`\n'
		banner += 'Use `!schedule help` for more information on available locations.'

	else:
		banner = 'A schedule has not been setup for this server yet.\n'
		banner += 'An admin may create one with `!config`.' 
	return banner


def override(message):
#Admin command to manually change a user's saved location
#Args should translate as: 1 id, 2 name, 3 locale
	if is_admin(message.author.roles):
		args = message.content.split()
		if len(args) != 5:
			return 'Formatting is: `!schedule override [USER.ID] [USER.NAME] [TIMEZONE]`'
		else:
			args = args[2:]
			locale = tzAbbrs.get(args[2].lower(), args[2])
			user = getUser(message.guild.id, int(args[0]))
			if user:
				with engine.connect() as conn:
					query = Users.update().where(and_(
						Users.c.id==args[0],
						Users.c.guild==message.guild.id,
						)).values(locale=locale)
					conn.execute(query)
				print('[+] {} UPDATED LOCALE TO {} FOR USER {}'.format(
					message.author, locale, args[1]))
				return 'Updated schedule location for {} to: {}'.format(args[1], locale)
			else:
				insertUser(args[0], message.guild, args[1], locale)
				print('[+] {} SETTING {}\'s SCHEDULE TO: {}'.format(
					message.author, args[1], locale))
				return 'Set schedule location for {} to: {}'.format(args[1], locale)


def setSchedule(message):
#User command to set their locale
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
	locale = server_locale if len(args) < 3 else tzAbbrs.get(args[2].lower(), args[2])
	user = getUser(message.guild.id, message.author.id)
	if user:
		with engine.connect() as conn:
			query = Users.update().where(and_(
				Users.c.id == message.author.id,
				Users.c.guild == message.guild.id)
				).values(locale = locale)
			conn.execute(query)
		return 'Updated your schedule location to: {}'.format(locale)
	else:
		insertUser(message.author.id, message.guild, message.author.name, locale)
		return 'Set your schedule location to: {}'.format(locale)


def insertUser(id_, guild_, name, locale):
	with engine.connect() as conn:
		ins = Users.insert().values(
			id = id_,
			name = name,
			locale = locale,
			guild = guild_.id,
			guild_name = guild_.name,
		)
		conn.execute(ins)


def getUser(guild_, id_):
	with engine.connect() as conn:
		select_st = select([Users]).where(Users.c.id == id_)
		res = conn.execute(select_st)
		result = res.fetchone()
		if result:
			return result
	
	
def load_config(guild):
	conn = engine.connect()	
	select_st = select([Config]).where(Config.c.id == guild)
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result
	return None
		

def getHelp(args, author):
	if len(args) < 3:
		banner = fetchFile('help', 'schedule')
		if not is_admin(author.roles):
			banner = banner.split('For Admins:')[0]
	else: #Get list of cities or continents
		banner = fetchFile('locales', args[2].lower())
	return banner
	
		
setup()
