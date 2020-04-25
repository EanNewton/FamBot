#!/usr/bin/python3

import requests
import urllib.request
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import aiofiles
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'wordoftheday.txt')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'output.txt')
url = 'https://www.wordsmith.org/words/today.html'
keywords = ['USAGE:\n', 'MEANING:\n', 'PRONUNCIATION:\n', 'ETYMOLOGY:\n', 'NOTES:\n']     
        
def readFile(path):
	with open(path, 'r') as f:
		return f.read()

def writeFile(content):
	with open(DEFAULT_PATH, 'w') as f:
		f.write(content)

def stripBlank():
	with open(DEFAULT_PATH) as f, open('output.txt', 'w') as outfile:
		for line in f:
			if line in keywords:
				line = '**'+line+'**'
			if not line.strip(): continue
			outfile.write(line)
		
async def getWebPage():
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200:
				print("[-] Status 200")
				text = await resp.read()
			else:
				print("[!] Status "+str(resp.status))
	soup = BeautifulSoup(text, "html.parser")
	text = soup.get_text()
	text = text.split('with Anu Garg')
	text = text[1].split('A THOUGHT FOR TODAY')
	text = text[0].strip()
	writeFile(text)
	stripBlank()
	return
	
async def getTodaysWord(toUpdate):
	if toUpdate:
		print('[+] Updating word of the day')
		await getWebPage()
	banner = readFile(OUTPUT_FILE)
	return banner
