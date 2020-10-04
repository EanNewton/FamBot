#!/usr/bin/python3

import asyncio
import aiohttp
import copy
import aiofiles
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from wiktionaryparser import WiktionaryParser
from googletrans import Translator, constants
import inflect

from tutil import fetchFile, debug, incrementUsage, wrap
from constants import DEFAULT_DIR, PATH_WOTD, URL_WOTD, URL_POTD, WOLFRAM, URL_WOLF_IMG, URL_WOLF_TXT, URL_KEYWORDS

parser = WiktionaryParser()
translator = Translator()


#Placeholder function for retry
def detectLanguage(message):
	"""
	Internal helper function for translate()
	:param message: <Discord.message object>
	:return: <List> 
	"""
	result = translator.translate(message.content)
	return [result.src, result.pronunciation, result.text]


#Placeholder function for retry
def directTranslate(text, src, target):
	"""
	Internal helper fucntion for translate()
	:param text: <String> The message to be translate
	:param src: <String> Language code for source language
	:param target: <String> Language code for destination language
	:return: <String> Translated message
	"""
	result = translator.translate(text, src=src, dest=target)
	return result.text


#TODO add retry on fail with list of words
def translate(message):
	"""
	Query Google Translate for a string, optionally including a target and source language
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'trans')
	args = message.content.split()
	
	if len(args) < 3:
		if len(args) > 1 and args[1] in  {'codes', 'langs', 'langcodes', 'languages'} and args[1] != 'help':
			return fetchFile('help', 'langcodes')
		return fetchFile('help', 'translate')

	else:
		text = ' '.join(args[1:])
		target = args[1][1:] if len(args) > 2 and args[1][0] == '-' else None
		source = args[2][1:] if len(args) > 3 and args[2][0] == '-' else None

		if target:
			if target not in constants.LANGUAGES:
				return 'Unknown target language `{}`. See `!tr langs` for full list.'.format(target)
			
			if source:
				if source not in constants.LANGUAGES:
					return 'Unknown source language `{}`. See `!tr langs` for full list.'.format(source)
				text = text.split(source, maxsplit=1)[1]
				result = translator.translate(text, src=source, dest=target)
			else:
				text = text.split(target, maxsplit=1)[1]
				result = translator.translate(text, dest=target)
		else:
			#Attempt to auto-detect source language and translate to English
			result = translator.translate(text)

		return '{}\nPronunciation: {}\nSource: {}\nTarget: {}'.format(
			result.text, 
			result.pronunciation, 
			constants.LANGUAGES[result.src], 
			constants.LANGUAGES[result.dest]
			)	


def wiki(message):
	"""
	Get the www.wiktionary.org entry for a word or phrase
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'dict')

	word = message.content.split(' ', maxsplit=1)[1]
	res = parser.fetch(word.strip())[0]

	etymology = res['etymology']
	definitions = res['definitions'][0]
	pronunciations = res['pronunciations']

	banner = '**{}**\n'.format(word)
	
	if definitions['partOfSpeech']:
		banner += '*Parts of Speech*\n{}\n'.format(definitions['partOfSpeech'])
	
	if etymology:
		banner += '*Etymology*\n{}\n'.format(etymology)
	
	if definitions['text']:
		banner += '*Definitions*\n'
		for each in definitions['text']:
			banner += '{} \n'.format(each)

	if definitions['relatedWords']:
		banner += '*Related Words*\n'
		for each in definitions['relatedWords']:
			for sub in each['words']:
				banner += '{}, '.format(sub)
			banner += '\n'

	if definitions['examples']:
		banner += '*Examples*\n'
		for each in definitions['examples']:
			banner += '{} \n'.format(each)

	if pronunciations['text'] or pronunciations['audio']:
		banner += '*Pronunciation*\n'
		for each in pronunciations['text']:
			banner += '{} \n'.format(each)

		for each in pronunciations['audio']:
			banner += 'https:{} \n'.format(each)

	#Discord has a character limit of 2000 per message
	#Wiktionary entries often exceed this limit
	#So we break it into a list and send each individually if it exceeds that limit
	return wrap(banner, 1990)


async def wolfram(message):
	"""
	Return an image based response from the Wolfram Alpha API
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'wolf')

	args = message.content.split()
	try:
		if args[1].lower() in {'simple', 'txt', 'text', 'textual'}:
			query_st = quote_plus(' '.join(args[2:]))
			query = URL_WOLF_TXT.format(WOLFRAM, query_st)
			
			async with aiohttp.ClientSession() as session:
				async with session.get(query) as resp:
					if resp.status == 200:
						text = await resp.read()
					elif resp.status == 501:
						return 'Wolfram cannot interpret your request.'
					else:
						return ['[!] Wolfram Server Status {}'.format(resp.status), None]

			text = text.decode('UTF-8')
			if len(text) > 1990:
				text = wrap(text, 1990)
			return [text, None]

		elif args[1].lower() in {'complex', 'graphic', 'graphical', 'image', 'img', 'gif'}:
			query_st = quote_plus(' '.join(args[2:]))
			query = URL_WOLF_IMG.format(WOLFRAM, query_st)
			filePath = '{}/log/wolf/{}.gif'.format(DEFAULT_DIR, message.id)
			
			async with aiohttp.ClientSession() as session:
				async with session.get(query) as resp:
					if resp.status == 200:
						f = await aiofiles.open(filePath, mode='wb')
						await f.write(await resp.read())
						await f.close()
						return [None, filePath]
					elif resp.status == 501:
						return ['Wolfram cannot interpret your request.', None]
					else:
						return ['[!] Wolfram Server Status {}'.format(resp.status), None]
		else:
			return [fetchFile('help', 'wolfram'), None]
	except:
		print('[!] Wolfram failed to process command on: {}'.format(message.content))
		return [fetchFile('help', 'wolfram'), None]


async def getTodaysWord(message):
	"""
	Pull the word of the day from www.wordsmith.org
	:param message: <Discord.message object> 
	:return: <str> Banner
	"""
	incrementUsage(message.guild, 'wotd')

	async with aiohttp.ClientSession() as session:
		async with session.get(URL_WOTD) as resp:
			if resp.status == 200:
				text = await resp.read()
			else:
				print("[!] Status {}".format(resp.status))
	
	soup = BeautifulSoup(text, "html.parser")
	text = soup.get_text()
	text = text.split('with Anu Garg')
	text = text[1].split('A THOUGHT FOR TODAY')
	text = text[0].strip()
	text = text.split('\n')
	
	banner = []
	for line in text:
		if line in URL_KEYWORDS.keys():
			banner.append(URL_KEYWORDS[line])
		else:
			banner.append(line)

	return '\n'.join([str(line) for line in banner if line])


async def getTodaysPoem(message):
	"""
	Pull the poem of the day from www.poems.com
	:param message: <Discord.message object> 
	:return: <str> Banner
	"""
	#TODO add column to usage table
	#incrementUsage(message.guild, 'potd')

	async with aiohttp.ClientSession() as session:
		async with session.get(URL_POTD) as resp:
			print(resp.status)
			if resp.status == 200:
				text = await resp.read()
			else:
				print("[!] Status {}".format(resp.status))

	soup = BeautifulSoup(text, "html.parser")
	title = str(soup.find("meta", property="og:title"))
	title = title.replace('<meta content=\'', '**')
	title = title.replace('\' property=\"og:title\"/>', '**')

	text = soup.find_all("span", class_="excerpt_line")
	text = [str(line).replace('</span>', '') for line in text]
	text = [line.replace('<span class=\"excerpt_line\">', '') for line in text]
	
	banner = [title]
	for line in text:
		if line in URL_KEYWORDS.keys():
			banner.append(URL_KEYWORDS[line])
		else:
			banner.append(line)

	return '\n'.join([str(line) for line in banner if line])


def google(message, iie=False):
	"""
	Return a link to a google search
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'google')
	query_st = quote_plus(message.content.split(' ', maxsplit=1)[1])
	if iie:
		banner = '<https://lmgtfy.com/?q={}&iie=1>'.format(query_st)
	else:
		banner = '<https://google.com/search?q={}>'.format(query_st)
	return banner


def getHelp(message):
	"""
	Return the help file located in ./docs/help
	:param message: <Discord.message object>
	:return: <String> The local help file
	"""
	incrementUsage(message.guild, 'help')
	return fetchFile('help', 'dict')
