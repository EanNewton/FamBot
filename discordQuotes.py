#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error
from discordUtils import debug, fetchFile, is_admin

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')
	
def sql_connection():
    try:
        con = sqlite3.connect(DEFAULT_PATH)
        return con
    except Error:
        print("[!] Error while connection ", Error)
 
def sql_table(con): 
	try:
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS famQuotes(id integer PRIMARY KEY, name, text, date)")
		con.commit()
	except Error:
		print("[!] Error while create ", Error)

@debug    
def sql_insert_quote(entities): 
	try:
		cursorObj = con.cursor()    
		cursorObj.execute('INSERT INTO famQuotes(id, name, text, date) VALUES(?, ?, ?, ?)', entities)
		con.commit()
		print("[+] Quote added... ", entities)
		return
	except Error:
		print("[!] Error while insert ", Error)

def sql_drop(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists famQuotes')
		con.commit()
	except Error:
		print("[!] Error while drop ", Error)
 
def sql_reset_quotedb(con):
	try:
		cursorObj = con.cursor()
		cursorObj.execute('DROP table if exists famQuotes')
		cursorObj.execute("CREATE TABLE IF NOT EXISTS famQuotes(id integer PRIMARY KEY, name, text, date)")
		con.commit()
		print("[+] TABLE famQuotes RESET")
	except Error:
		print("[!] Error while drop ", Error)

@debug
def delete_quote(arg):
	try:
		sql = 'DELETE FROM famQuotes WHERE id=?'
		cur = con.cursor()
		cur.execute(sql, (arg,))
		con.commit()
		if check_if_exists(arg):
			print("[!] Failed to remove quote")
			return("Failed to remove quote")
		else:
			print("[+] Removed quote.")
			return "Successfully removed quote."
	except Error:
		print("[!] Error while delete ", Error)

@debug     
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
		print("[!] Error while fetch rand", Error)
	
@debug		   
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
		return str(quote) + '\n ---' + str(author) + ' on ' + str(date)
	except Error:
		print("[!] Error while fetch rand", Error)

@debug		
def get_help(author):
	banner = fetchFile('help', 'quotes')
	if is_admin(author.roles):
		banner += "React to a message with ❌ to remove it."
	return banner
	
@debug
def helper(args, author):
	if len(args) > 1:
		if args[1] == 'help':
			return get_help(author.roles)
		else:
			return fetchQuote(args[1])
	else:
		return fetchQuote(-1)

global con
con = sql_connection()
sql_table(con)
