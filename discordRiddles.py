#!/usr/bin/python3

import random
from discordUtils import debug, is_admin, fetchFile
from sqlalchemy import create_engine, desc, select, MetaData, Table, Column, Integer, String 

@debug		
def helper(message, author):
	args = message.content.split()
	operator = 'get'
	if len(args) > 1:
		operator = args[1]
	return {
		'solve': lambda: checkAnswer(message, author),
		'delete': lambda: deleteRiddle(args[2]),
		'score': lambda: getScore(author.id),
		'add': lambda: insertRiddle(message),
		'get': lambda: getNewRiddle(args, author),
		'help': lambda: getHelp(author),
		'reset': lambda: reset(author.roles),
		#'leaderboard': lambda: getLeaderboard(args),
	}.get(operator, lambda: None)()
		
def getHelp(author):
	banner = fetchFile('help', 'riddles')
	if is_admin(author.roles):
		banner += "`!riddle delete RIDDLE.ID` remove a riddle.\n"
		banner += "`!riddle reset` DANGEROUS! delete all users and all riddles.\n"
	return banner	
	
def setup():
	global engine, meta, rUsers, Riddles
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

def reset(author):
	if is_admin(author):
		conn = engine.connect()
		query = Riddles.drop(engine)
		query = rUsers.drop(engine)
		setup()
		print("[!] TABLE filters RESET")

@debug
def checkExists(id_, table):
	result = None
	conn = engine.connect()	
	select_st = select([table]).where(
		table.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchall()
	return result is not None

@debug	
def insertUser(entity):
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
def insertRiddle(message):
#Command format should be:
#!riddle add Name: riddle text ||solution text||
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
	return "Added riddle #{} as:\n**{}**\n{}".format(str(message.id), name, riddle)
	
@debug
def incScore(userID, riddleID):
	conn = engine.connect()
	user = getEntry(userID, rUsers)
	score = user[3]+1
	solved = user[4]+str(riddleID)+";"
	ins = rUsers.update().where(rUsers.c.id==userID).values(
		score = score,
		solved = solved,
	)	
	conn.execute(ins)
	
@debug
def checkSolved(userID, riddleID):
	conn = engine.connect()
	user = getEntry(userID, rUsers)
	solvedSet = set(user[4].split(";"))
	return riddleID in solvedSet

@debug
def getEntry(id_, table):
	result = None
	conn = engine.connect()	
	select_st = select([table]).where(table.c.id == id_)
	res = conn.execute(select_st)
	result = res.fetchone()
	return result

@debug		
def getScore(userID):
	user = getEntry(userID, rUsers)
	if user:
		return "{}\'s score is: {}".format(user[1], str(user[3]))
	
@debug	
def getNewRiddle(riddleID, author):	
	conn = engine.connect()	
	if not checkExists(author.id, rUsers):
		entity = [author.id, author.name, riddleID, 0, "START;"]
		insertUser(entity)
	user = getEntry(author.id, rUsers)
	solvedSet = set(user[4].split(";"))
	
	select_st = select([Riddles])
	res = conn.execute(select_st)
	result = res.fetchall()
	for each in result:
		if str(each[0]) not in solvedSet:
			#each[0]: ID, [1]: name, [2]: text
			return "Riddle #{}\n**{}**\n{}".format(str(each[0]), each[1], each[2])
	else:	
		return "Congratulations! You have completed all available riddles! Check back soon or add a new one yourself."
	
@debug
def checkAnswer(message, author):
	args = message.content.split()
	riddleID = args[2]
	solution = args[3:]
	solution = ' '.join(solution)
	
	if checkExists(riddleID, Riddles):
		riddle = getEntry(riddleID, Riddles)
	else: 
		return "Riddle does not exist, check ID"
	if not checkExists(author.id, rUsers):
		entity = [author.id, author.name, riddleID, 0, "START;"]
		insertUser(entity)
		
	if solution[:2] == '||' and solution[-2:] == '||':
		if solution[2:-2] == riddle[3]:
			if checkSolved(author.id, riddleID):
				return "You have already solved this riddle."
			else:
				incScore(author.id, riddleID)
				return "Solved! " + str(getScore(author.id))
		else:
			return "Incorrect"
	else:
		banner = "Remember to spoiler tag your solution by putting `||` on both ends.\n"
		banner += "Example: `!riddle solve RIDDLE.ID ||your solution here||`"
		return banner

def deleteRiddle(id_):
	conn = engine.connect()
	ins = Riddles.delete().where(Riddles.c.id == id_,)
	conn.execute(ins)
	return "Deleted riddle"

setup()			
		
'''
#broken
@debug		
def getLeaderboard(args):
	limit = 10 if len(args) != 3 else args[2]
	print(limit)
	banner = ''
	conn = engine.connect()	
	select_st = select([Riddles]).order_by(Riddles.c.score.desc())
	print(select_st)
	res = conn.execute(select_st)
	result = res.fetchall()
	print(result)
	if result:
		for count in range(limit):
			banner += str(result[count][1])+": "+str(result[count][3])+"\n"
		return banner
	else:
		return None

#Old version of function
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
'''
