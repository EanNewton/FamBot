#TODO:
#Make config user friendly
#Clean up code



#!/usr/bin/python3

from discordUtils import debug, fetchFile, writeFile, is_admin
from sqlalchemy import create_engine, and_, update, select, MetaData, Table, Column, Integer, String 
import pendulum

divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 
#Timezone Abbreviations for user convenience
#e.g. convert 'jst' to 'Asia/Tokyo'
tzAbbrs = {} 
with open('./docs/locales/abbr.txt', 'r') as f:
	for line in f:
		(key, val) = line.split(',')
		val = val.strip('\n')
		tzAbbrs[key] = val

	
def load_config(guild):
	conn = engine.connect()	
	select_st = select([Config]).where(Config.c.id == guild)
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result
	return None


def helper(message):
	args = message.content.split()
	ops = {'get', 'set', 'help', 'override', 'config'}
	operator = 'get'
	if len(args) > 1:
		#if args[1] == 'drop' and is_admin(message.author.roles):
		#	reset()
		if args[1] in ops:
			operator = args[1]
	return {
		'get': lambda: getSchedule(message),
		'set': lambda: setSchedule(message),
		'help': lambda: getHelp(args, message.author),
		'override': lambda: override(message),
		#'config': lambda: set_config(message),
	}.get(operator, lambda: None)()	


def getSchedule(message):
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
		hours = []
		dict_ = {}
		mySchedHours = []
		mySched = []
		for day in days:
			hours.append(day.split('='))
		for each in hours:
			if each[0] != '':
				if each[1] != '':
					dict_[int(each[0])] = each[1].split(',')
		for each in dict_.items():
			print(each)
			for hour in each[1]:
				if ':' in hour:
					hour = hour.split(':')
				if hour != '' or hour != ' ':
					mySchedHours.append(hour)
				mySched.append(pendulum.now(tz=server_locale).add(days=each[0]))

		#Needed for handling partial weeks, ie so we don't post a message with only 1 or 2 days
		mySchedDup = mySched.copy()
		#Show current server time vs current user time
		banner = '{} in {}\n'.format(dt.to_day_datetime_string(), dt.timezone_name)
		banner += '{} in {}\n'.format(now_in_server.to_day_datetime_string(), server_locale)
		banner += divider

		while(mySched[0].day_of_week != pendulum.MONDAY):
			for day in range(len(mySched)):
				mySched[day] = mySched[day].add(days=1)

		if now_in_server.day_of_week != pendulum.MONDAY:	
			#Get us to Monday
			while(mySchedDup[0].day_of_week != pendulum.MONDAY):
				for day in range(len(mySchedDup)):
					mySchedDup[day] = mySchedDup[day].add(days=-1)
			
			for day in range(len(mySchedDup)):
				if isinstance(mySchedHours[day], list):
					#Contains minutes
					mySchedDup[day] = mySchedDup[day].at(int(mySchedHours[day][0]), int(mySchedHours[day][1]))
				else:
					mySchedDup[day] = mySchedDup[day].at(int(mySchedHours[day]))
				#Convert timezone and add to message
				mySchedDup[day] = mySchedDup[day].in_tz(dtLocalName)
				if mySchedDup[day].format('DDDD') >= dt.format('DDDD'):
					if mySchedDup[day].format('DDDD') == dt.format('DDDD'):
						banner += '**{}**\n'.format(mySchedDup[day].to_day_datetime_string())
					else:
						banner += '{}\n'.format(mySchedDup[day].to_day_datetime_string())
			
		for day in range(len(mySched)):
			if isinstance(mySchedHours[day], list):
				#Contains minutes
				mySched[day] = mySched[day].at(int(mySchedHours[day][0]), int(mySchedHours[day][1]))
			else:
				mySched[day] = mySched[day].at(int(mySchedHours[day]))
			#Convert timezone and add to message
			mySched[day] = mySched[day].in_tz(dtLocalName)
			if mySched[day].format('DDDD') == dt.format('DDDD'):
				banner += '**{}**\n'.format(mySched[day].to_day_datetime_string())
			else:
				banner += '{}\n'.format(mySched[day].to_day_datetime_string())
		banner += divider
		banner += 'Come hang with us at: <{}>\n'.format(url)	
		banner += divider
		banner += 'You can set your schedule location with `!schedule set LOCATION`\n'
		banner += 'Use `!schedule help` for more information on available locations.'

	else:
		banner = 'A schedule has not been setup for this server yet.\n'
		banner += 'An admin may create one with `!config`.' 
	return banner


def override(message):
	args = message.content.split()
	args = args[2:]
#Admin command to manually change a user's saved location
# Args should translate as: 1 id, 2 name, 3 locale
	if is_admin(message.author.roles) and len(args) == 3:
		locale = tzAbbrs.get(args[2].lower(), args[2])
		user = getUser(message.guild.id, int(args[0]))
		if user:
			conn = engine.connect()	
			query = Users.update().where(and_(
				Users.c.id==args[0],
				Users.c.guild==message.guild.id,
				)).values(locale=locale)
			results = conn.execute(query)
			print('[+] {} UPDATED LOCALE TO {} FOR USER {}'.format(message.author, locale, args[1]))
			return 'Updated schedule location for {} to: {}'.format(args[1], locale)
		else:
			insertUser(args[0], message.guild, args[1], locale)
			print('[+] {} SETTING {}\'s SCHEDULE TO: {}'.format(message.author, args[1], locale))
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
		conn = engine.connect()	
		query = Users.update().where(and_(
			Users.c.id==message.author.id,
			Users.c.guild==message.guild.id)).values(locale=locale)
		results = conn.execute(query)
		return 'Updated your schedule location to: {}'.format(locale)
	else:
		insertUser(message.author.id, message.guild, message.author.name, locale)
		return 'Set your schedule location to: {}'.format(locale)


def getHelp(args, author):
	if len(args) < 3:
		banner = fetchFile('help', 'schedule')
		if is_admin(author.roles):
			banner += '`!schedule override USER.ID USER.NAME LOCATION` to change a user\'s set location.\n' 
		return banner
	else: #Get list of cities or continents
		return fetchFile('locales', args[2].lower())
				
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
	print('[+] End schedule Setup')


def insertUser(id_, guild_, name, locale):
	conn = engine.connect()
	ins = Users.insert().values(
		id = id_,
		name = name,
		locale = locale,
		guild = guild_.id,
		guild_name = guild_.name,
	)
	res = conn.execute(ins)
	return True


def getUser(guild_, id_):
	conn = engine.connect()	
	select_st = select([Users]).where(Users.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result
	return None

def reset():
	conn = engine.connect()
	query = Users.drop(engine)
	setup()
	print("[!] TABLE schedule RESET")
		
setup()
