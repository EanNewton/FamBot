#!/usr/bin/python3

import asyncio
import aiohttp
import copy
import aiofiles
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from discord import Embed
from wiktionaryparser import WiktionaryParser
from googletrans import Translator, constants
import inflect

import timeout
from tutil import fetchFile, debug, incrementUsage, wrap
from constants import DEFAULT_DIR, PATH_WOTD, URL_WOTD, URL_POTD, WOLFRAM, URL_WOLF_IMG, URL_WOLF_TXT, URL_KEYWORDS
from constants import help_dict

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
			help_ = fetchFile('help', 'langcodes')
			banner = Embed(title="Translator Help", description="Language Codes")
			banner.set_footer(text=help_)
		else:
			help_ = fetchFile('help', 'translate')
			banner = Embed(title="Translator Help")
			banner.add_field(name="Commands", value=help_)

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

		banner = Embed(title="Google Translate")
		banner.add_field(name="Original Text", value=text, inline=False)
		banner.add_field(name="Translated Text", value=result.text, inline=False)
		banner.add_field(name="Source Language", value=constants.LANGUAGES[result.src], inline=True)
		banner.add_field(name="Target Language", value=constants.LANGUAGES[result.dest], inline=True)
		
	return banner


def yandex(message):
	args = message.content.split()
	if len(args) < 2:
		return 'Please supply a URL to an image.'
	yandex = '<https://yandex.com/images/search?url={}&rpt=imageview>'.format(quote_plus(args[1]))
	tineye = 'https://tineye.com'
	return '{}\n{}'.format(yandex, tineye)


def wiki(message):
	"""
	Get the www.wiktionary.org entry for a word or phrase
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'dict')
	args = message.content.split()
	if len(args) == 1 or args[1] == 'help':
		banner = Embed(title="Wiktionary Help")
		banner.add_field(name='About', value=help_dict['main'])
		banner.add_field(name='Aliased Command Names', value=help_dict['alternative'])
		return banner
	else:
		try:
			word = message.content.split(' ', maxsplit=1)[1]
			result = parser.fetch(word.strip())[0]
			etymology = result['etymology']
			definitions = result['definitions'][0]
			pronunciations = result['pronunciations']

			banner = Embed(title="Wiktionary", description=word)
			
			if definitions['partOfSpeech']:
				banner.add_field(name="Parts of Speech", value=definitions['partOfSpeech'], inline=False)

			if etymology:
				banner.add_field(name="Etymology", value=etymology, inline=False)
			
			if definitions['text']:
				defs = ''
				for each in definitions['text']:
					defs += '{} \n'.format(each)
				banner.add_field(name="Definitions", value=defs, inline=False)

			if definitions['relatedWords']:
				defs = ''
				for each in definitions['relatedWords']:
					for sub in each['words']:
						defs += '{}, '.format(sub)
					defs += '\n'
				banner.add_field(name="Related Words", value=defs, inline=False)

			if definitions['examples']:
				defs = ''
				for each in definitions['examples']:
					defs += '{} \n'.format(each)
				banner.add_field(name="Examples", value=defs, inline=False)

			if pronunciations['text'] or pronunciations['audio']:
				defs_text = ''
				defs_audio = ''
				for each in pronunciations['text']:
					defs_text += '{} \n'.format(each)

				for each in pronunciations['audio']:
					defs_audio += 'https:{} \n'.format(each)
				banner.add_field(name="Pronunciation, IPA", value=defs_text, inline=False)
				banner.add_field(name="Pronunciation, Audio Sample", value=defs_audio, inline=False)

			return banner
		except:
			return None


#TODO update help to embed
async def wolfram(message):
	"""
	Return an image based response from the Wolfram Alpha API
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
	incrementUsage(message.guild, 'wolf')

	args = message.content.split()
	banner = Embed(title="Wolfram Alpha")
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
			banner.add_field(name=' '.join(args[2:]), value=text)
			return banner

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
		return None


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
	
	fields = {'header': '',}
	for idx, line in enumerate(text):
		if line:
			if line in URL_KEYWORDS.keys():
				fields[line] = ''
				key = line
			elif idx == 0:
				fields['header'] = '{}\n{}'.format(fields['header'], line)
			else:
				fields[key] = '{}\n{}'.format(fields[key], line)

	banner = Embed(title="Word of the Day", description=fields['header'])
	fields.pop('header')
	for key, val in fields.items():
		banner.add_field(name=key, value=val)
	banner.set_footer(text=URL_WOTD)

	return banner


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
	text = [line.replace('<em>', '*') for line in text]
	text = [line.replace('</em>', '*') for line in text]
	text = '\n'.join(text)
	
	banner = Embed(title='Poem of the Day')
	banner.add_field(name=title, value=text)
	banner.set_footer(text=URL_POTD)
	return banner


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
	return wrap(fetchFile('help', 'dict'), 1990)
