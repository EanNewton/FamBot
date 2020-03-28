#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'filters.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

blacklistLow = {"jap"}
blacklistStrict = {"xxx"}

divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 

def importBlacklists():
	path = DEFAULT_DIR+'/blacklists/blacklist_ethnic.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistLow.add(line.strip())
			blacklistStrict.add(line.strip())
	path = DEFAULT_DIR+'/blacklists/blacklist_sex.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistLow.add(line.strip())
			blacklistStrict.add(line.strip())
	path = DEFAULT_DIR+'/blacklists/blacklist_ru.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistLow.add(line.strip())
			blacklistStrict.add(line.strip())	
	path = DEFAULT_DIR+'/blacklists/blacklist_1716.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistStrict.add(line.strip())
	#Custom
	path = DEFAULT_DIR+'/blacklists/blacklist_custom_strict.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistStrict.add(line.strip())
	path = DEFAULT_DIR+'/blacklists/blacklist_custom_low.txt'
	with open(path, 'r') as f:
		for line in f:
			blacklistLow.add(line.strip())

def getBlacklistLow():
	return blacklistLow

def getBlacklistStrict():
	return blacklistStrict
	
def addWord(level, word):
	print(level + " " + word)
	if level == '1':
		print("Adding "+word)
		path = DEFAULT_DIR+'/blacklists/blacklist_custom_low.txt'
		with open(path, 'a') as f:
			f.write(word)
	if level == '2':
		print("Adding "+word)
		path = DEFAULT_DIR+'/blacklists/blacklist_custom_strict.txt'
		with open(path, 'a') as f:
			f.write(word)
	return "Success."
			
def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        return con
    except Error:
        print("Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS filters(id integer PRIMARY KEY, level)")
		con.commit()
	except Error:
		print("Error while create ", Error)
    
def sql_insert_filter(con, entities): 
	exists = getFilter(entities[0])
	if exists == "Filter level: not set":
		try:
			cursorObj = con.cursor()    
			cursorObj.execute('INSERT INTO filters(id, level) VALUES(?, ?)', entities)
			con.commit()
			return "Set filter for current channel to "+str(entities[1])
		except Error:
			print("Error while insert ", Error)
	else:
		delete_filter(con, entities[0])
		sql_insert_filter(con, entities)
	return "Set filter for current channel to: "+str(entities[1])

def delete_filter(con, arg):
	print("in delete filter")
	print(arg)
	try:
		sql = 'DELETE FROM filters WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (int(arg),))
		con.commit()
		print("deleted")
		return "Successfully removed filter."
	except Error:
		print("Error while delete ", Error)

def sql_drop(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists filters')
		con.commit()
	except Error:
		print("Error while drop ", Error)
 
def sql_reset_filters(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists filters')
		cursorObj.execute("CREATE TABLE IF NOT EXISTS filters(id integer PRIMARY KEY, level)")
		con.commit()
		return "All filters reset."
	except Error:
		print("Error while drop ", Error)

def getFilter(toFetch):	
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM filters WHERE id=? LIMIT 1', (str(toFetch),))
		result = cursorObj.fetchall()
		if not result:
			level = "not set"
		else:
			level = result[0][1]
		return "Filter level: "+str(level)
	except Error:
		print("Error while fetch filter", Error)
		
def helper(operator, args):
	print("in helper")
	print(args)
	return {
		'get': lambda: getFilter(args),
		'set': lambda: sql_insert_filter(con, args),
		'clear': lambda: sql_insert_filter(con, [args, 0]),
		'clearAll': lambda: sql_reset_filters(con),
		'help': lambda: getHelp(),
		'add': lambda: addWord(args[0], args[1]),
	}.get(operator, lambda: None)()

def getHelp():
	banner = "**Filter Help**\n"+divider
	banner += "`!filter get` check the current channel\s filter level.\n"
	banner += "`!filter set LEVEL` set a filter level for the current channel. "
	banner += "Options are 1 for Low or 2 for Strict.\n"
	banner += "`!filter clearall` clear all channel\'s filters.\n"
	banner += "`!filter add LEVEL WORD` add a word to the filter. "
	banner += "Currently only supports single words without spaces.\n\n"
	return banner

global con
con = sql_connection()
sql_table(con)
