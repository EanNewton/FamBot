#!/usr/bin/python3

from discordUtils import debug, fetchFile, is_admin
from sqlalchemy import create_engine, update, select, MetaData, Table, Column, Integer, String 
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

def helper(args, author):
	ops = {'get', 'set', 'help', 'override'}
	operator = 'get'
	if len(args) > 1:
		if args[1] == 'drop' and is_admin(author.roles):
			reset()
		elif args[1] in ops:
			operator = args[1]
	return {
		'get': lambda: getSchedule(args, author),
		'set': lambda: setSchedule(args, author),
		'help': lambda: getHelp(args, author),
		'override': lambda: override(args[2:], author),
	}.get(operator, lambda: None)()	

def getSchedule(args, author):
	locale = 'Asia/Tokyo' #Default case
	if len(args) > 1: #User requested specific location
		locale = tzAbbrs.get(args[1].lower(), args[1])
	else: #Checking for saved locale in DB
		user = getUser(author.id)
		if user:
			locale = user[0][2]	
	
	dt = pendulum.now(tz=locale)
	dtLocalName = dt.timezone.name
	now_in_tokyo = pendulum.now(tz='Asia/Tokyo')
	mySchedHours = [10, 10, 16, 10, 16]
	mySched = [
		pendulum.now(tz='Asia/Tokyo'), #monday
		pendulum.now(tz='Asia/Tokyo').add(days=1), #tuesday
		pendulum.now(tz='Asia/Tokyo').add(days=2), #wednesday
		pendulum.now(tz='Asia/Tokyo').add(days=4), #friday
		pendulum.now(tz='Asia/Tokyo').add(days=5) #saturday
	]
	mySchedDup = mySched.copy()

	banner = dt.to_day_datetime_string() + ' in '+ dt.timezone_name +'\n'
	banner += now_in_tokyo.to_day_datetime_string() + ' in Tokyo \n'
	banner += divider
	
	while(mySched[0].day_of_week != pendulum.MONDAY):
		for day in range(len(mySched)):
			mySched[day] = mySched[day].add(days=1)
	
	if now_in_tokyo.day_of_week != pendulum.MONDAY:	
		while(mySchedDup[0].day_of_week != pendulum.MONDAY):
			for day in range(len(mySchedDup)):
				mySchedDup[day] = mySchedDup[day].add(days=-1)
		
	if now_in_tokyo.day_of_week != pendulum.MONDAY:	
		for day in range(len(mySchedDup)):
			mySchedDup[day] = mySchedDup[day].at(mySchedHours[day])
			mySchedDup[day] = mySchedDup[day].in_tz(dtLocalName)
			if mySchedDup[day].format('DDDD') >= dt.format('DDDD'):
				if mySchedDup[day].format('DDDD') == dt.format('DDDD'):
					banner += '**'+mySchedDup[day].to_day_datetime_string()+'**\n'
				else:
					banner += mySchedDup[day].to_day_datetime_string()+'\n'
		
	for day in range(len(mySched)):
		mySched[day] = mySched[day].at(mySchedHours[day])
		mySched[day] = mySched[day].in_tz(dtLocalName)
		if mySched[day].format('DDDD') == dt.format('DDDD'):
			banner += '**'+mySched[day].to_day_datetime_string()+'**\n'
		else:
			banner += mySched[day].to_day_datetime_string()+'\n'
		
	banner += divider
	banner += 'You can set your schedule location with `!schedule set LOCATION`\n'
	banner += 'Use `!schedule help` for more information on available locations.'
	return banner

def override(args, author):
#Admin command to manually change a user's saved location
# Args should translate as: 1 id, 2 name, 3 locale
	if is_admin(author.roles) and len(args) == 3:
		locale = tzAbbrs.get(args[2].lower(), args[2])
		user = getUser(int(args[0]))
		if user:
			conn = engine.connect()	
			query = Users.update().where(Users.c.id==args[0]).values(locale=locale)
			results = conn.execute(query)
			print('[+] '+str(author)+' UPDATED LOCALE TO ' + str(locale)+ ' FOR USER '+str(args[1]))
			return 'Updated schedule location for '+str(args[1])+' to: '+str(locale)
		else:
			insertUser(args[0], args[1], locale)
			print('[+] '+str(author)+' SETTING '+str(args[1])+'\'s SCHEDULE TO: '+locale)
			return 'Set schedule location for '+str(args[1])+' to: '+str(locale)


def setSchedule(args, author):
	#if no location provided default to Tokyo
	locale = 'Asia/Tokyo' if len(args) < 3 else tzAbbrs.get(args[2].lower(), args[2])
	user = getUser(author.id)
	if user:
		conn = engine.connect()	
		query = Users.update().where(Users.c.id==author.id).values(locale=locale)
		results = conn.execute(query)
		return 'Updated your schedule location to: '+str(locale)
	else:
		insertUser(author.id, author.name, locale)
		return 'Set your schedule location to: '+str(locale)

def getHelp(args, author):
	if len(args) < 3:
		banner = fetchFile('help', 'schedule')
		if is_admin(author.roles):
			banner += '`!schedule override USER.ID USER.NAME LOCATION` to change a user\'s set location.\n' 
		return banner
	else: #Get list of cities or continents
		return fetchFile('locales', args[2].lower())
				
def setup():
	global engine, meta, Users
	engine = create_engine('sqlite:///./log/quotes.db', echo = False)
	meta = MetaData()
	Users = Table(
		'schedule', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('locale', String),
		)
	meta.create_all(engine)
	print('[+] End schedule Setup')
	
def insertUser(id_, name, locale):
	conn = engine.connect()
	ins = Users.insert().values(
		id = id_,
		name = name,
		locale = locale,
	)
	conn.execute(ins)

def getUser(id_):
	conn = engine.connect()	
	select_st = select([Users]).where(
		Users.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	if result:
		return result
	return None

def reset():
	conn = engine.connect()
	query = Users.drop(engine)
	setup()
	print("[!] TABLE schedule RESET")
		
setup()
