#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, is_admin, fetchFile
from sqlalchemy import create_engine, select, MetaData, Table, Column, Integer, String 
from sqlalchemy.sql import exists 	

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')

def setup():
	global engine
	global meta
	global rUsers
	global Riddles
	engine = create_engine('sqlite:///./log/quotes.db', echo = True)
	meta = MetaData()
	rUsers = Table(
		'riddlesUsers', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('current', String),
		Column('score', Integer),
		Column('solved', String),
		)
	Riddles = Table(
		'riddles', meta,
		Column('id', Integer, primary_key = True),
		Column('name', String),
		Column('text', String),
		Column('solution', String),
		)
	meta.create_all(engine)
	print('[+] End riddle Setup')

@debug
def alch_checkUserExists(id_):
	conn = engine.connect()	
	select_st = select([rUsers]).where(
		rUsers.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	if result:
		return True
	else:
		return False
@debug
def alch_checkRiddleExists(id_):
	conn = engine.connect()	
	select_st = select([Riddles]).where(
		Riddles.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	if result:
		return True
	else:
		return False

@debug	
def alch_insertUser(entity):
	(id_, name, current, score, solved) = entity
	conn = engine.connect()
	ins = rUsers.insert().values(
		id = id_,
		name = name,
		current = current,
		score = score,
		solved = solved,
	)
	conn.execute(ins)

@debug	
def alch_insertRiddle(message):
	args = message.content.split()
	name = ' '.join(args[2:])
	name = name.split(':')
	name = name[0]
	riddle = message.content.split(':')
	riddle = ' '.join(riddle[1:])
	riddle = riddle.split('||')
	riddle = riddle[0].strip()
	solution = message.content.split('||')
	solution = solution[1].lower()
	
	conn = engine.connect()
	ins = Riddles.insert().values(
		id = message.id,
		name = name,
		text = riddle,
		solution = solution,
	)
	conn.execute(ins)
	return "Added riddle #"+str(message.id)+" as: \n**"+name+"**\n "+riddle
	
@debug
def check_answer(message, author):
	args = message.content.split()
	riddleID = args[2]
	solution = args[3:]
	solution = ' '.join(solution)
	riddleExists = alch_checkRiddleExists(riddleID)
	userExists = alch_checkUserExists(author.id)	
	
	if riddleExists:
		riddle = alch_getRiddle(riddleID)
	else:
		return "Riddle does not exist, check ID"
	if not userExists:
		entity = [author.id, author.name, riddleID, 0, "START;"]
		alch_insertUser(entity)
		
	if solution[:2] == '||' and solution[-2:] == '||':
		if solution[2:-2] == riddle[3]:
			if alch_checkSolved(author.id, riddleID):
				return "You have already solved this riddle."
			else:
				alch_incScore(author.id, riddleID)
				return "Solved! " + str(get_score(author.id))
		else:
			return "Incorrect"
	else:
		banner = "Remember to spoiler tag your solution by putting `||` on both ends.\n"
		banner += "Example: `!riddle solve RIDDLE.ID ||your solution here||`"
		return banner

@debug
def alch_incScore(userID, riddleID):
	conn = engine.connect()
	user = alch_getUser(userID)
	score = user[3]+1
	solved = user[4]+str(riddleID)+";"
	ins = rUsers.update().where(rUsers.c.id==userID).values(
		score = score,
		solved = solved,
	)	
	conn.execute(ins)
	
@debug
def alch_checkSolved(userID, riddleID):
	conn = engine.connect()
	user = alch_getUser(userID)
	solvedSet = set(user[4].split(";"))
	if riddleID in solvedSet:
		return True
	else:
		return False

@debug
def alch_getUser(id_):
	conn = engine.connect()	
	select_st = select([rUsers]).where(rUsers.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchone()
	if result:
		return result
	else:
		return None	

@debug		
def get_score(userID):
	user = alch_getUser(userID)
	if user:
		return user[1]+"\'s score is: "+str(user[3])

@debug			
def get_leaderboard(args):
	limit = 10 if len(args) != 3 else args[2]
	banner = ''
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers ORDER BY score DESC LIMIT ?', (limit,))
		result = cursorObj.fetchall()
		if result:
			for user in range(len(result)):
				banner += str(result[user][1])+": "+str(result[user][3])+"\n"
			return banner
		else:
			return None
	except Error:
		print("[!] Error while get user score")

@debug		
def alch_getRiddle(riddleID):
	conn = engine.connect()	
	select_st = select([Riddles]).where(Riddles.c.id == riddleID)
	res = conn.execute(select_st)
	result = res.fetchone()
	print(result)
	if result:
		return result
	else:
		return None			
	
@debug	
def fetch_riddle_name(riddleID, author):	
	conn = engine.connect()	
	if not alch_checkUserExists(author.id):
		entity = [author.id, author.name, riddleID, 0, "START;"]
		alch_insertUser(entity)
	user = alch_getUser(author.id)
	solvedSet = set(user[4].split(";"))
	
	select_st = select([Riddles])#.order_by(func.random())
	res = conn.execute(select_st)
	result = res.fetchall()
	for each in result:
		if str(each[0]) not in solvedSet:
			riddleID = each[0]
			name = each[1]
			text = each[2]
			return "Riddle #"+str(riddleID)+"\n**"+str(name)+"**\n"+str(text)
	else:	
		return "Congratulations! You have completed all available riddles! Check back soon or add a new one yourself."


@debug
def fetch_user_id(toFetch):		
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if not result:
			return False
		else:
			return True
	except Error:
		print("[!] Error while fetch rand", Error)

@debug		   
def fetch_user_name(toFetch):		
	try:
		cursorObj = con.cursor()
		if toFetch == -1:
			cursorObj.execute('SELECT * FROM riddlesUsers WHERE id IN (SELECT id FROM riddlesUsers ORDER BY RANDOM() LIMIT 1)')

		else:
			cursorObj.execute('SELECT * FROM riddlesUsers WHERE name=? ORDER BY RANDOM() LIMIT 1', (str(toFetch),))
		result = cursorObj.fetchall()
		text = result[0][2]
		name = result[0][1]
		solution = result[0][3]
		return str(text) + '\n ---' + str(name) + ' on ' + str(solution)
	except Error:
		print("[!] Error while fetch rand", Error)
		 
#Dangerous 
def sql_reset_riddledb(con, args, author):
	if args[2] == 'YES' and is_admin(author.roles):
		try:
			cursorObj = con.cursor()
			cursorObj.execute('DROP table if exists riddles')
			cursorObj.execute('DROP table if exists riddlesUsers')
			con.commit()
			sql_table(con)
			print("[+] TABLE riddles & riddlesUsers RESET")
			return "Deleted riddles database."
		except Error:
			print("[!] Error while drop ", Error)

def delete_riddle(con, arg, author):
	if is_admin(author.roles):
		arg = arg[2]
		try:
			print("Trying to delete riddle")
			sql = 'DELETE FROM riddles WHERE id=?'
			cur = con.cursor()
			cur.execute(sql, (arg,))
			con.commit()
			print("[+] Removed riddle.")
			return "Successfully removed riddle."
		except Error:
			print("[!] Error while delete ", Error)

def delete_user(con, arg):
	try:
		sql = 'DELETE FROM riddlesUsers WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (arg,))
		con.commit()
		print("[+] Removed riddle user.")
		return "Successfully removed user."
	except Error:
		print("[!] Error while delete ", Error)

@debug		
def helper(message, author):
	args = message.content.split()
	if len(args) == 1:
		operator = 'get'
	elif len(args) > 1:
		operator = args[1]
	return {
		'solve': lambda: check_answer(message, author),
		'delete': lambda: delete_riddle(con, args, author),
		'score': lambda: get_user_score(author.id),
		'add': lambda: alch_insertRiddle(message),
		'get': lambda: fetch_riddle_name(args, author),
		'getUser': lambda: fetch_riddle_name(args),
		'help': lambda: get_help(author),
		'exists': lambda: fetch_user_id(args),
		'reset': lambda: sql_reset_riddledb(con, args, author),
		'leaderboard': lambda: get_leaderboard(args),
	}.get(operator, lambda: None)()
		
def get_help(author):
	banner = fetchFile('help', 'riddles')
	if is_admin(author.roles):
		banner += "`!riddle delete RIDDLE.ID` remove a riddle.\n"
		banner += "`!riddle reset` DANGEROUS! delete all users and all riddles.\n"
	return banner	

setup()	
