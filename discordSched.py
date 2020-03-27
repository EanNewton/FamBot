#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
import pendulum

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

mySchedHours = [10, 10, 16, 10, 16]
	
tzAbbrs = [
	['jst', 'Asia/Tokyo'],
	['est', 'America/New_York'],
	['pst', 'America/Los_Angeles'],
	['hst', 'Pacific/Honolulu'],
	['china', 'Asia/Shanghai'],
	['hk', 'Asia/Hong_Kong'],
	['utc', 'Europe/London'],
	['aest', 'Australia/Sydney'],
	['cst', 'America/Chicago'],
	['ast', 'America/Puerto_Rico'],
	['canada', 'America/Vancouver'],
	['korea', 'Asia/Seoul'],
	['nz', 'Pacific/Aukland'],
	['nzdt', 'Pacific/Aukland'],
	['india', 'Asia/Kolkata'],
	['new york', 'America/New_York'],
	['new-york', 'America/New_York'],
	['los-angeles', 'America/Los_Angeles'],
	['los angeles', 'America/Los_Angeles']
	]
	
adminRoles = ['admin', 'mod', 'discord mod']
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
		mySchedDup = [
			pendulum.now(tz='Asia/Tokyo'), #monday
			pendulum.now(tz='Asia/Tokyo').add(days=1), #tuesday
			pendulum.now(tz='Asia/Tokyo').add(days=2), #wednesday
			pendulum.now(tz='Asia/Tokyo').add(days=4), #friday
			pendulum.now(tz='Asia/Tokyo').add(days=5) #saturday
		]
		mySchedDupSec = [
			pendulum.now(tz='Asia/Tokyo'), #monday
			pendulum.now(tz='Asia/Tokyo').add(days=1), #tuesday
			pendulum.now(tz='Asia/Tokyo').add(days=2), #wednesday
			pendulum.now(tz='Asia/Tokyo').add(days=4), #friday
			pendulum.now(tz='Asia/Tokyo').add(days=5) #saturday
		]
		dt = pendulum.now(tz=locale)
		dtLocalName = dt.timezone.name
		now_in_tokyo = pendulum.now(tz='Asia/Tokyo')
		banner = dt.to_day_datetime_string() + ' in '+ dt.timezone_name +'\n'
		banner += now_in_tokyo.to_day_datetime_string() + ' in Tokyo \n'
		banner += divider
		
		while(mySchedDup[0].day_of_week != pendulum.MONDAY):
			for day in range(0, len(mySchedDup)):
				mySchedDup[day] = mySchedDup[day].add(days=1)
			
		while(mySchedDupSec[0].day_of_week != pendulum.MONDAY):
			for day in range(0, len(mySchedDupSec)):
				mySchedDupSec[day] = mySchedDupSec[day].add(days=-1)
					
		for day in range(0, len(mySchedDupSec)):
			mySchedDupSec[day] = mySchedDupSec[day].at(mySchedHours[day])
			mySchedDupSec[day] = mySchedDupSec[day].in_tz(dtLocalName)
			if mySchedDupSec[day].format('DDDD') >= dt.format('DDDD'):
				if mySchedDupSec[day].format('DDDD') == dt.format('DDDD'):
					banner += '**'+mySchedDupSec[day].to_day_datetime_string()+'**\n'
				else:
					banner += mySchedDupSec[day].to_day_datetime_string()+'\n'
						
		for day in range(0, len(mySchedDup)):
			mySchedDup[day] = mySchedDup[day].at(mySchedHours[day])
			mySchedDup[day] = mySchedDup[day].in_tz(dtLocalName)
			if mySchedDup[day].format('DDDD') == dt.format('DDDD'):
				banner += '**'+mySchedDup[day].to_day_datetime_string()+'**\n'
			else:
				banner += mySchedDup[day].to_day_datetime_string()+'\n'

		# For if the user does not have a tz saved in .db yet		
		if extended:
			banner += divider
			banner += 'You can set your schedule location with `!schedule set LOCATION`\n'
			banner += 'Use `!schedule help` for more information.'
		return banner
	except e:
		print(e)

def get_sched_help(locale, admin):
	if locale == 'default':
		banner = '**Schedule Help**\n'+divider
		if admin:
			banner += '`!schedule override USER.ID USER.NAME LOCATION` to change a user\'s set location.\n' 
		banner += '`!schedule` to see the schedule for your default location.\n'
		banner += '`!schedule CONTINENT/CITY` to see the schedule for another location.\n'
		banner += '`!schedule help CONTINENT` to see cities for that location.\n'
		banner += '`!schedule set CONTINENT/CITY` to change your default location.\n'
		banner += divider+'Continents include: \n'+get_sched_help('continents', admin)
		return banner
	else:
		path = DEFAULT_DIR+'/locales/'+locale+'.txt'
		with open(path, 'r') as f:
			result = f.read()
			return str(result)
	
def is_admin(author):
	for roles in author:
		if str(roles).lower() in adminRoles:
			return True
	return False

def helper(operator, args, author):
	return {
		'get': lambda: getSched(args, author),
		'set': lambda: setSched(args, author),
		'help': lambda: get_sched_help(args, author),
		'override': lambda: override(args, author),
	}.get(operator, lambda: None)()

def override(args, author):
	if is_admin(author.roles):
		if len(args) == 3:
			try:
				# args is 1 id, 2 name, 3 locale
				for index in range(0, len(tzAbbrs)):
					if args[2] == tzAbbrs[index][0]:
						locale = tzAbbrs[index][1]
						break
					else:
						locale = args[2]
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
		else:
			return 'Format is [user.id] [user.name] [locale]'

def setSched(args, author):
	if len(args) > 0:
		for index in range(0, len(tzAbbrs)):
			if args == tzAbbrs[index][0]:
				locale = tzAbbrs[index][1]
				break
			else:
				locale = args
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
	if args:
		for index in range(0, len(tzAbbrs)):
			if args[0].lower() == tzAbbrs[index][0]:
				locale = tzAbbrs[index][1]
				break
			else:
				locale = args[0]
		banner = get_schedule(locale, True)
		return str(banner)
	else:
		try:
			cursorObj = con.cursor()
			c = cursorObj.execute("""SELECT EXISTS (SELECT 1 FROM schedule WHERE id=? LIMIT 1)""", (author, )).fetchone()[0]
			if c:
				cursorObj.execute('SELECT locale FROM schedule WHERE id=?', (author,))
				result = cursorObj.fetchone()	
				banner = get_schedule(result[0], False)
				return str(banner)
			else:
				locale = 'Asia/Tokyo'
				banner = get_schedule(locale, True)
				return str(banner)
		except Error:
			print('Error while fetch time')

global con
con = sql_connection()
sql_table(con)
