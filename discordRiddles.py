#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, is_admin, fetchFile

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')

@debug
def check_answer(con, message, author):
	args = message.content.split()
	riddleID = args[2]
	solution = args[3:]
	solution = ' '.join(solution)
	riddleExists = check_riddle_exists(riddleID)
	userExists = check_user_exists(author.id)
	
	if riddleExists:
		riddle = fetch_riddle_id(riddleID)
	else:
		return "Riddle does not exist, check ID"
	if userExists == False:
		solved = "START;"
		entity = [author.id, author.name, riddleID, 0, solved]
		sql_insert_user(con, entity)
	
	if solution[:2] == '||' and solution[-2:] == '||':
		if solution[2:-2] == riddle[0][3]:
			if has_solved(con, author.id, riddleID):
				return "You have already solved this riddle."
			else:
				increment_score(con, author.id, riddleID)
				return "Solved! " + str(get_user_score(author.id))
		else:
			return "Incorrect"
	else:
		banner = "Remember to spoiler tag your solution by putting `||` on both ends.\n"
		banner += "Example: `!riddle solve RIDDLE.ID ||your solution here||`"
		return banner
		

@debug
def increment_score(con, toFetch, riddleID):
	user = get_user(toFetch)
	userScore = user[3] + 1
	solved = user[4]+str(riddleID)+";"
	entity = [user[0], user[1], user[2], userScore, solved]
	delete_user(con, toFetch)
	sql_insert_user(con, entity)
	
@debug	
def has_solved(con, userID, riddleID):
	user = get_user(userID)
	solvedSet = user[4].split(";")
	if riddleID in solvedSet:
		return True
	return False

@debug		
def get_user(toFetch):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if result:
			return result[0]
		else:
			return None
	except Error:
		print("[!] Error while get user")

@debug		
def get_user_score(toFetch):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddlesUsers WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if result:
			return str(result[0][1])+"\'s score is: "+str(result[0][3])
		else:
			return None
	except Error:
		print("[!] Error while get user score")

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
		print("[!] Error while fetch rand", Error)	

@debug	
def check_riddle_exists(toFetch):	
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddles WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if not result:
			return False
		else:
			return True
	except Error:
		print("[!] Error while fetch rand", Error)

@debug	
def check_user_exists(toFetch):		
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
def sql_insert_user(con, entities): 
	try:
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO riddlesUsers(id, name, current, score, solved) VALUES(?, ?, ?, ?, ?)', entities)
		con.commit()
		print("[+] Added riddle user... ", entities)
		return
	except Error:
		print("[!] Error while insert ", Error)

@debug		
def set_user_current(con, riddleID, userID):
	user = get_user(userID)
	entity = [user[0], user[1], riddleID, user[3], user[4]]
	delete_user(con, userID)
	sql_insert_user(con, entity)
	return

@debug
def get_user_current(con, author):
	return get_user(author.id)[2]

@debug	
def fetch_riddle_name(toFetch, author):		
	if check_user_exists(author.id) == False:
		solved = "START;"
		entity = [author.id, author.name, 0, 0, solved]
		sql_insert_user(con, entity)
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM riddles')
		rows = len(cursorObj.fetchall())
		count = 0
		flag = True
		while flag:
			cursorObj.execute('SELECT * FROM riddles WHERE id IN (SELECT id FROM riddles ORDER BY RANDOM() LIMIT 1)')
			result = cursorObj.fetchall()
			flag = has_solved(con, author.id, result[0][0])
			count = count + 1
			if count > rows:
				return "Congratulations! You have completed all available riddles! Check back soon or add a new one yourself."

		riddleID = result[0][0]
		text = result[0][2]
		name = result[0][1]
		set_user_current(con, riddleID, author.id) 
		return "Riddle #"+str(riddleID)+"\n**"+str(name)+"**\n"+str(text)
	except Error:
		print("[!] Error while fetch rand", Error)

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
	
@debug    
def sql_insert_riddle(con, message, author): 
	try:
		args = message.content.split()
		#id, name, text, solution
		name = ' '.join(args[2:])
		name = name.split(':')
		name = name[0]
		solution = message.content.split('||')
		solution = solution[1].lower()
		
		riddle = message.content.split(':')
		riddle = riddle[1].split('||')
		riddle = riddle[0].strip()
		
		entity = [message.id, name, riddle, solution]
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO riddles(id, name, text, solution) VALUES(?, ?, ?, ?)', entity)
		con.commit()
		print("[+] Added riddle... ", entity)
		return "Added new riddle "+str(entity[1])+" as riddle #"+str(entity[0])
	except Error:
		print("[!] Error while insert ", Error)
		
def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        print('[+] Connection establish')
        return con
    except Error:
        print("[!] Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS riddles(id integer PRIMARY KEY, name, text, solution)")
		cursorObj.execute("CREATE TABLE IF NOT EXISTS riddlesUsers(id integer PRIMARY KEY, name, current, score, solved)")
		con.commit()
		print("[+] Tables created")
	except Error:
		print("[!] Error while create ", Error)
		 
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
		'solve': lambda: check_answer(con, message, author),
		'delete': lambda: delete_riddle(con, args, author),
		'score': lambda: get_user_score(author.id),
		'add': lambda: sql_insert_riddle(con, message, author),
		'addUser': lambda: sql_insert_user(con, args, author),
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
	
global con
con = sql_connection()
sql_table(con)
