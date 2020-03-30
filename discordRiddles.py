#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error

debug = True

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
 
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 	
adminRoles = {'admin', 'mod', 'discord mod'}
		
def helper(operator, args, author):
	if debug:
		print(divider)
		print("In helper")
		print(args)
	return {
		'check': lambda: check_answer(con, args, author),
		'clear': lambda: delete_quote(con, args),
		'score': lambda: get_user_score(author.id),
		'addRiddle': lambda: sql_insert_riddle(con, args, author),
		'addUser': lambda: sql_insert_user(con, args, author),
		'getRiddle': lambda: fetch_riddle_name(args, author),
		'getUser': lambda: fetch_riddle_name(args),
		'help': lambda: get_help(author),
		'exists': lambda: fetch_user_id(args),
		'reset': lambda: sql_reset_riddledb(con),
		'leaderboard': lambda: get_leaderboard(args),
	}.get(operator, lambda: None)()

def is_admin(author):
	for roles in author:
		if str(roles).lower() in adminRoles:
			return True
	return False

def check_answer(con, args, author):
	if debug:
		print(divider)
		print("In check answer")
		print(args)
	riddleExists = check_riddle_exists(args[0])
	userExists = check_user_exists(author.id)
	if riddleExists:
		riddle = fetch_riddle_id(args[0])
	else:
		return "Riddle does not exist, check ID"
	if userExists == False:
		print("User not found, creating user profile")
		solved = "START;"
		entity = [author.id, author.name, args[0], 0, solved]
		sql_insert_user(con, entity)
	
	if args[1][:2] == '||' and args[1][-2:] == '||':
		if args[1].strip('||') == riddle[0][3]:	
			if has_solved(con, author.id, args[0]):
				return "You have already solved this riddle."
			else:
				increment_score(con, author.id, args[0])
				return "Solved! " + str(get_user_score(author.id))
		else:
			banner = "Remember to spoiler tag your solution by putting `||` on both ends.\n"
			banner += "Example: `!riddle solve RIDDLE.ID ||your solution here||`"
	else:
		return "Incorrect"

def increment_score(con, toFetch, riddleID):
	if debug:
		print(divider)
		print("in increment score")
		print(toFetch)
	user = get_user(toFetch)
	userScore = user[3]
	userScore = userScore + 1
	solved = user[4]
	solved = solved+str(riddleID)+";"
	entity = [user[0], user[1], user[2], userScore, solved]
	delete_user(con, toFetch)
	sql_insert_user(con, entity)
	
def has_solved(con, userID, riddleID):
	if debug:
		print(divider)
		print("in has solved")
		print(userID)
		print(riddleID)
	user = get_user(userID)
	print("found user")
	solvedSet = user[4].split(";")
	if riddleID in solvedSet:
		print("has solved")
		return True
	print("has not solved")
	return False
		
def get_user(toFetch):
	if debug:
		print(divider)
		print("in get user")
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if result:
			return result[0]
		else:
			return None
	except Error:
		print("Error while get user")
		
def get_user_score(toFetch):
	if debug:
		print(divider)
		print("in get user score")
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if result:
			return str(result[0][1])+"\'s score is: "+str(result[0][3])
		else:
			return None
	except Error:
		print("Error while get user score")
			
def get_leaderboard(limit):
	if debug:
		print(divider)
		print("in get leaders")
	if limit == None:
		limit = 10
	banner = ''
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers ORDER BY score DESC LIMIT ?', (limit,))
		result = cursorObj.fetchall()
		if result:
			for user in range(0, len(result)):
				banner += str(result[user][1])+": "+str(result[user][3])+"\n"
			return banner
		else:
			return None
	except Error:
		print("Error while get user score")
		
def fetch_riddle_id(toFetch):		
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddles WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if result:
			return result 
		else:
			return None
	except Error:
		print("Error while fetch rand", Error)	
	
def check_riddle_exists(toFetch):	
	if debug:
		print(divider)
		print("in check riddle exists")	
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddles WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if not result:
			return False
		else:
			return True
	except Error:
		print("Error while fetch rand", Error)
	
def check_user_exists(toFetch):		
	if debug:
		print(divider)
		print("in check user exists")
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if not result:
			return False
		else:
			return True
	except Error:
		print("Error while fetch rand", Error)

def sql_insert_user(con, entities): 	
	if debug:
		print("in insert user")
		print(entities)	
	try:
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO riddlesUsers(id, name, current, score, solved) VALUES(?, ?, ?, ?, ?)', entities)
		con.commit()
		print("Added... ", entities)
		return
	except Error:
		print("Error while insert ", Error)
		
def set_user_current(con, riddleID, userID):
	if debug:
		print(divider)
		print("in set user current")
		print(riddleID)
	user = get_user(userID)
	entity = [user[0], user[1], riddleID, user[3], user[4]]
	delete_user(con, userID)
	sql_insert_user(con, entity)
	return

def get_user_current(con, author):
	if debug:
		print(divider)
		print("in get user current")
	user = get_user(author.id)
	return user[2]
	
def fetch_riddle_name(toFetch, author):		
	if debug:
		print(divider)
		print("In fetch by name")
		print(toFetch)
	if check_user_exists(author.id) == False:
		print("User not found, creating user profile")
		solved = "START;"
		entity = [author.id, author.name, 0, 0, solved]
		sql_insert_user(con, entity)
	try:
		cursorObj = con.cursor()
		if toFetch == 'current':
			toFetch = get_user_current(con, author)
			if toFetch == -1:
				return "You have not started yet, use `!riddle get` to get your first riddle.\n Check `!riddle help` for options."
			else:
				cursorObj.execute('SELECT * FROM riddles WHERE id=? ORDER BY RANDOM() LIMIT 1', (str(toFetch),))	
				result = cursorObj.fetchall()
		else:
			flag = True
			#cursorObj.execute('SELECT Count(*) FROM riddles')
			cursorObj.execute('SELECT * FROM riddles')
			rows = len(cursorObj.fetchall())
			count = 0
			while flag:
				if debug:
					print("in while")
					print(flag)
					print(count)
					print(rows)
				cursorObj.execute('SELECT * FROM riddles WHERE id IN (SELECT id FROM riddles ORDER BY RANDOM() LIMIT 1)')
				result = cursorObj.fetchall()
				#print("FETCHED")
				#print(result)
				flag = has_solved(con, author.id, result[0][0])
				count = count + 1
				if count > rows:
					return "Congratulations! You have completed all available riddles! Check back soon or add a new one yourself."

		print("broke from while")
		riddleID = result[0][0]
		text = result[0][2]
		name = result[0][1]
		set_user_current(con, riddleID, author.id) 
		banner = "Riddle #"+str(riddleID)+"\n**"+str(name)+"**\n"+str(text)
		return str(banner)
	except Error:
		print("Error while fetch rand", Error)

    
def sql_insert_riddle(con, entities, author): 	
	if debug:
		print(divider)
		print("In insert")
		print(entities)	
	try:
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO riddles(id, name, text, solution) VALUES(?, ?, ?, ?)', entities)
		con.commit()
		print("Added... ", entities)
		return "Added new riddle "+str(entities[1])+" as riddle #"+str(entities[0])
	except Error:
		print("Error while insert ", Error)
		
#######	
def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        return con
    except Error:
        print("Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS riddles(id integer PRIMARY KEY, name, text, solution)")
		cursorObj.execute("CREATE TABLE IF NOT EXISTS riddlesUsers(id integer PRIMARY KEY, name, current, score, solved)")
		con.commit()
	except Error:
		print("Error while create ", Error)
		 
#Dangerous 
def sql_reset_riddledb(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists riddles')
		cursorObj.execute('DROP table if exists riddlesUsers')
		con.commit()
		sql_table(con)
		print("[!] TABLE riddles & riddlesUsers RESET")
	except Error:
		print("Error while drop ", Error)

def delete_riddle(con, arg):
	try:
		sql = 'DELETE FROM riddles WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (arg,))
		con.commit()
		print("[!] Removed riddle.")
		return "Successfully removed riddle."
	except Error:
		print("Error while delete ", Error)

def delete_user(con, arg):
	if debug:
		print(divider)
		print("in delete user")
	try:
		sql = 'DELETE FROM riddlesUsers WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (arg,))
		con.commit()
		print("[!] Removed riddle user.")
		return "Successfully removed user."
	except Error:
		print("Error while delete ", Error)

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
		print("Error while fetch rand", Error)
		   
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
		banner = str(text) + '\n ---' + str(name) + ' on ' + str(solution)
		return str(banner)
	except Error:
		print("Error while fetch rand", Error)
		
def get_help(author):
	banner = "**Riddle Help**\n"+divider
	banner += "`!riddle get` get a riddle.\n"
	banner += "`!riddle get current` redisplay last riddle you got.\n"
	banner += "`!riddle solve RIDDLE.ID ||SOLUTION||` solve a riddle.\n"
	banner += "`!riddle score` get your score.\n"
	banner += "`!riddle leaderboard NUMBER` get the top X users, or leave blank for top 10.\n"
	banner += "`!riddle add TITLE: TEXT ||SOLUTION||` add a new riddle.\n"
	if is_admin(author.roles):
		banner += "`!riddle delete RIDDLE.ID` remove a riddle.\n"
		banner += "`!riddle reset` DANGEROUS! delete all users and all riddles.\n"
	return banner
	
global con
con = sql_connection()
sql_table(con)
