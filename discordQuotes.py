#!/usr/bin/python3

import os
import random
import sqlite3
from sqlite3 import Error

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
 
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

global con
con = sql_connection()
sql_table(con)
