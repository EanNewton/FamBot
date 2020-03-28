#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
 
divider = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 	
adminRoles = {'admin', 'mod', 'discord mod'}

def is_admin(author):
	for roles in author:
		if str(roles).lower() in adminRoles:
			return True
	return False
	
def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        return con
    except Error:
        print("Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS famQuotes(id integer PRIMARY KEY, name, text, date)")
		con.commit()
	except Error:
		print("Error while create ", Error)
    
def sql_insert_quote(con, entities): 
	#entity = [reaction.message.id, userName[:-5], reaction.message.content, str(timeStamp)]		
	try:
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO famQuotes(id, name, text, date) VALUES(?, ?, ?, ?)', entities)
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
 
def sql_reset_quotedb(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists famQuotes')
		cursorObj.execute("CREATE TABLE IF NOT EXISTS famQuotes(id integer PRIMARY KEY, name, text, date)")
		con.commit()
		print("TABLE famQuotes RESET")
	except Error:
		print("Error while drop ", Error)

def delete_quote(con, arg):
	try:
		sql = 'DELETE FROM famQuotes WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (arg,))
		con.commit()
		print("Removed quote.")
		return "Successfully removed quote."
	except Error:
		print("Error while delete ", Error)
     
def check_if_exists(toFetch):		
	try:
		cursorObj = con.cursor()
		cursorObj.execute('SELECT * FROM famQuotes WHERE id=? LIMIT 1', (toFetch,))
		result = cursorObj.fetchall()
		if not result:
			return False
		else:
			return True
	except Error:
		print("Error while fetch rand", Error)
		   
def fetchQuote(toFetch):		
	try:
		cursorObj = con.cursor()
		if toFetch == -1:
			cursorObj.execute('SELECT * FROM famQuotes WHERE id IN (SELECT id FROM famQuotes ORDER BY RANDOM() LIMIT 1)')

		else:
			cursorObj.execute('SELECT * FROM famQuotes WHERE name=? ORDER BY RANDOM() LIMIT 1', (str(toFetch),))
		result = cursorObj.fetchall()
		quote = result[0][2]
		author = result[0][1]
		date = result[0][3]
		banner = str(quote) + '\n ---' + str(author) + ' on ' + str(date)
		return str(banner)
	except Error:
		print("Error while fetch rand", Error)
		
def get_help(admin):
	admin = is_admin(admin.roles)
	banner = "**Quote Help**\n"+divider
	banner += "`!quote` pull up a random quote.\n"
	banner += "`!quote USER` pull up a quote from a specific user. "
	banner += "This is the user\'s full username, not their server nickname. "
	banner += "It is case sensitive.\n"
	banner += "React to a message with 🗨 to add it to the database.\n"
	if admin:
		banner += "React to a message with ❌ to remove it.\n\n"
	return banner
		
def helper(operator, args):
	return {
		'clear': lambda: delete_quote(con, args),
		'add': lambda: sql_insert_quote(con, args),
		'get': lambda: fetchQuote(con, args),
		'help': lambda: get_help(args),
		'exists': lambda: check_if_exists(args),
	}.get(operator, lambda: None)()
	
global con
con = sql_connection()
sql_table(con)
