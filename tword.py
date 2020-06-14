#!/usr/bin/python3
#TODO Add time check to prevent web scraping if < 24 hours

import os
import time
import asyncio
import aiohttp
import aiofiles

from bs4 import BeautifulSoup
from wiktionaryparser import WiktionaryParser

from tutil import fetchFile, debug

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './docs/wordoftheday.txt')
url = 'https://www.wordsmith.org/words/today.html'
keywords = {'USAGE:\n', 'MEANING:\n', 'PRONUNCIATION:\n', 'ETYMOLOGY:\n', 'NOTES:\n'}
parser = WiktionaryParser()


def wiki(word):
	banner = str()
	res = parser.fetch(word.strip())[0]
	etymology = res['etymology']
	definitions = res['definitions'][0]
	pronunciations = res['pronunciations']
	
	banner += '**{}** \n'.format(definitions['partOfSpeech'])
	banner += '*Etymology*\n{}\n'.format(etymology)
	banner += '*Definitions*\n'
	for each in definitions['text']:
		banner += '{} \n'.format(each)
	banner += '*Related Words*\n'
	for each in definitions['relatedWords']:
		for sub in each['words']:
			banner += '{}, '.format(sub)
		banner += '\n'
	banner += '*Examples*\n'
	for each in definitions['examples']:
		banner += '{} \n'.format(each)
	banner += '*Pronunciation*\n'
	for each in pronunciations['text']:
		banner += '{} \n'.format(each)
	for each in pronunciations['audio']:
		banner += 'https:{} \n'.format(each)
		
	return wrap(banner, 1990)

def wrap(s, w):
    return [s[i:i + w] for i in range(0, len(s), w)]

		
async def getTodaysWord():
	lastMod = os.path.getmtime('./docs/output.txt')
	if time.strftime('%b %d', time.localtime(lastMod)) != time.strftime('%b %d'):
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


def stripBlank():
	with open(DEFAULT_PATH) as f, open('./docs/output.txt', 'w') as outfile:
		for line in f:
			if line in keywords:
				line = '**{}**'.format(line)
			if not line.strip(): continue
			outfile.write(line)
	
	
	
def getHelp():
	return fetchFile('help', 'dict')
