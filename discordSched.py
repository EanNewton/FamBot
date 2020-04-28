#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, fetchFile, is_admin
import pendulum

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')

tzAbbrs = {
	'jst': 'Asia/Tokyo',
	'est': 'America/New_York',
	'pst': 'America/Los_Angeles',
	'hst': 'Pacific/Honolulu',
	'china': 'Asia/Shanghai',
	'hk': 'Asia/Hong_Kong',
	'utc': 'Europe/London',
	'aest': 'Australia/Sydney',
	'cst': 'America/Chicago',
	'ast': 'America/Puerto_Rico',
	'canada': 'America/Vancouver',
	'korea': 'Asia/Seoul',
	'nz': 'Pacific/Aukland',
	'nzdt': 'Pacific/Aukland',
	'india': 'Asia/Kolkata',
	'new york': 'America/New_York',
	'new-york': 'America/New_York',
	'ny': 'America/New_York',
	'nyc': 'America/New_York',
	'la': 'America/Los_Angeles',
	'los-angeles': 'America/Los_Angeles',
	'los angeles': 'America/Los_Angeles'
	}
		
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        return con
    except Error:
        print("Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS schedule(id integer PRIMARY KEY, name, locale)")
		con.commit()
	except Error:
		print("Error while create ", Error)
    
def sql_insert_sched(con, entities): 
	try:
		cursorObj = con.cursor()   
		cursorObj.execute('INSERT INTO schedule(id, name, locale) VALUES(?, ?, ?)', entities)
		con.commit()
		print("Added... ", entities)
		return
	except Error:
		print("Error while insert ", Error)
 
def sql_drop(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists famQuotes')
		con.commit()
	except Error:
		print("Error while drop ", Error)

def sql_reset_scheddb(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists schedule')
		cursorObj.execute("CREATE TABLE IF NOT EXISTS schedule(id integer PRIMARY KEY, name, locale)")
		con.commit()
		print("TABLE schedule RESET")
	except Error:
		print("Error while drop ", Error)

def get_schedule(locale, extended):
	try:
		mySchedHours = [10, 10, 16, 10, 16]
		mySched = [
			pendulum.now(tz='Asia/Tokyo'), #monday
			pendulum.now(tz='Asia/Tokyo').add(days=1), #tuesday
			pendulum.now(tz='Asia/Tokyo').add(days=2), #wednesday
			pendulum.now(tz='Asia/Tokyo').add(days=4), #friday
			pendulum.now(tz='Asia/Tokyo').add(days=5) #saturday
		]
		mySchedDup = mySched.copy()
		
		dt = pendulum.now(tz=locale)
		dtLocalName = dt.timezone.name
		now_in_tokyo = pendulum.now(tz='Asia/Tokyo')
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
		# For if the user does not have a tz saved in .db yet		
		if extended:
			banner += divider
			banner += 'You can set your schedule location with `!schedule set LOCATION`\n'
			banner += 'Use `!schedule help` for more information on available locations.'
		return banner
	except e:
		print(e)

def override(args, author):
# Args should translate as: 1 id, 2 name, 3 locale
	if is_admin(author.roles) and len(args) == 3:
		try:
			locale = tzAbbrs.get(args[2].lower(), args[2])
			cursorObj = con.cursor()
			c = cursorObj.execute("""SELECT EXISTS (SELECT 1 FROM schedule WHERE id=? LIMIT 1)""", (args[0], )).fetchone()[0]
			if c:
				cursorObj.execute('UPDATE schedule SET locale = ? WHERE id = ?', (locale, args[0],))
				con.commit()
				print(str(author)+' UPDATED LOCALE TO ' + str(locale)+ ' FOR USER '+str(args[1]))
				return 'Updated schedule location for '+str(args[1])+' to: '+str(locale)
			else:
				print(str(author)+' SETTING '+str(args[1])+'\'s SCHEDULE TO: '+locale)
				entity = [int(args[1]), str(args[2]), str(locale)]
				sql_insert_sched(con, entity)
				return 'Set schedule location for '+str(args[1])+' to: '+str(locale)
		except Error:
			print('Error while override ', Error)

def setSched(args, author):
	locale = 'Asia/Tokyo' if len(args) < 3 else tzAbbrs.get(args[2].lower(), args[2])
	cursorObj = con.cursor()
	c = cursorObj.execute("""SELECT EXISTS (SELECT 1 FROM schedule WHERE id=? LIMIT 1)""", (author.id, )).fetchone()[0]
	if c:
		cursorObj.execute('UPDATE schedule SET locale = ? where id = ?', (locale, author.id,))
		con.commit()
		print('UPDATED LOCALE TO ' + str(locale)+ ' FOR USER '+str(author))
		return 'Updated your schedule location to: '+str(locale)
	else:
		entity = [int(message.author.id), str(author), str(locale)]
		sql_insert_sched(con, entity)
		print('SETTING '+str(message.author)+'\'s SCHEDULE TO: '+locale)
		return 'Set your schedule location to: '+str(locale)

def getSched(args, author):
	locale = 'Asia/Tokyo'
	if len(args) > 1:
		locale = tzAbbrs.get(args[1].lower(), args[1])
	else:
		try:
			cursorObj = con.cursor()
			c = cursorObj.execute("""SELECT EXISTS (SELECT 1 FROM schedule WHERE id=? LIMIT 1)""", (author, )).fetchone()[0]
			if c:
				cursorObj.execute('SELECT locale FROM schedule WHERE id=?', (author,))
				locale = cursorObj.fetchone()[0]
				print(locale)
		except Error:
			print('Error while fetch time')
	return get_schedule(locale, True)


def helper(args, author):
	operator = 'get'
	if len(args) > 1:
		operator = args[1]
	return {
		'get': lambda: getSched(args, author.id),
		'set': lambda: setSched(args, author),
		'help': lambda: get_help(args, author),
		'override': lambda: override(args[2:], author),
	}.get(operator, lambda: None)()	

def get_help(args, author):
	if len(args) < 3:
		banner = fetchFile('help', 'schedule')
		if is_admin(author.roles):
			banner += '`!schedule override USER.ID USER.NAME LOCATION` to change a user\'s set location.\n' 
		return banner
	else:
		return fetchFile('locales', args[2].lower())
			
global con
con = sql_connection()
sql_table(con)
