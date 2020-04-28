#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, fetchFile

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/filters.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))

blacklistLow = {"jap"}
blacklistStrict = {"xxx"}

def check(message):
	text = message.content.split()
	fLevel = getFilter(message.channel.id)
	lists = {'Filter level: 2': (blacklistStrict), 'Filter level: 1': (blacklistLow)}
	if fLevel in lists:
		for word in text:
			if word in lists[fLevel]:
				return True
	return False

def importBlacklists():
	listOfFiles_low = list()
	listOfFiles_high = list()
	for (dirpath, dirnames, filenames) in os.walk(DEFAULT_DIR+'/blacklists'):
		if 'low' in dirpath:
			listOfFiles_low += [os.path.join(dirpath, file) for file in filenames]
		if 'strict' in dirpath:
			listOfFiles_high += [os.path.join(dirpath, file) for file in filenames]
	
	for file_ in listOfFiles_low:
		with open(file_, 'r') as f:
			for line in f:
				blacklistLow.add(line.strip())
				blacklistStrict.add(line.strip())
	for file_ in listOfFiles_high:
		with open(file_, 'r') as f:
			for line in f:
				blacklistStrict.add(line.strip())
	blacklistStrict.remove('')
	print("[+] Imported Filter Blacklists")

def addWord(level, word):
	path = None
	if level == '1':
		path = DEFAULT_DIR+'/blacklists/low/blacklist_custom.txt'
	elif level == '2':
		path = DEFAULT_DIR+'/blacklists/high/blacklist_custom.txt'
	if path:
		with open(path, 'a') as f:
			f.write(word)
			print("[!] Added "+word+" to level "+level+" custom filters")
			return "Success"
	return "Error"
			
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
	
def helper(message):
	args = message.content.split()
	operator = args[1].lower()
	return {
		'get': lambda: getFilter(message.channel.id),
		'set': lambda: sql_insert_filter(con, [message.channel.id, args[2]]),
		'clear': lambda: sql_insert_filter(con, [message.channel.id, 0]),
		'clearall': lambda: sql_reset_filters(con),
		'help': lambda: get_help(),
		'add': lambda: addWord(args[2], args[3:]),
	}.get(operator, lambda: None)()

def get_help():
	return fetchFile('help', 'filters')

global con
con = sql_connection()
sql_table(con)
