#!/usr/bin/python3
#TODO Add time check to prevent web scraping if < 24 hours

import os
import asyncio
import aiohttp
import aiofiles

from bs4 import BeautifulSoup

from tutil import fetchFile

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './docs/wordoftheday.txt')
url = 'https://www.wordsmith.org/words/today.html'
keywords = {'USAGE:\n', 'MEANING:\n', 'PRONUNCIATION:\n', 'ETYMOLOGY:\n', 'NOTES:\n'}     


def stripBlank():
	with open(DEFAULT_PATH) as f, open('./docs/output.txt', 'w') as outfile:
		for line in f:
			if line in keywords:
				line = '**{}**'.format(line)
			if not line.strip(): continue
			outfile.write(line)
		
async def getTodaysWord():
	print('[+] Updating word of the day')
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as resp:
			if resp.status == 200:
				text = await resp.read()
			else:
				print("[!] Status {}".format(resp.status))
	
	soup = BeautifulSoup(text, "html.parser")
	text = soup.get_text()
	text = text.split('with Anu Garg')
	text = text[1].split('A THOUGHT FOR TODAY')
	text = text[0].strip()
	
	with open(DEFAULT_PATH, 'w') as f:
		f.write(text)
	stripBlank()
	return fetchFile('.', 'output')
