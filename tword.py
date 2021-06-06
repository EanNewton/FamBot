#!/usr/bin/python3

import aiohttp
import aiofiles
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from discord import Embed
from wiktionaryparser import WiktionaryParser

from tutil import fetch_file, increment_usage, wrap
from constants import DEFAULT_DIR, URL_WOTD, WOLFRAM, URL_WOLF_IMG, URL_WOLF_TXT, URL_KEYWORDS, VERBOSE
from constants import help_dict


parser = WiktionaryParser()


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
    increment_usage(message.guild, 'dict')
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
        except Exception as e:
            if VERBOSE >= 0:
                print('[!] Exception in wiki: {}'.format(e))
            return None


# TODO update help to embed
async def wolfram(message):
    """
	Return an image based response from the Wolfram Alpha API
	:param message: <Discord.message object> 
	:return: <str> Banner or None
	"""
    increment_usage(message.guild, 'wolf')

    args = message.content.split()
    banner = Embed(title="Wolfram Alpha")
    try:
        if len(args) > 1:
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
                file_path = '{}/log/wolf/{}.gif'.format(DEFAULT_DIR, message.id)

                async with aiohttp.ClientSession() as session:
                    async with session.get(query) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open(file_path, mode='wb')
                            await f.write(await resp.read())
                            await f.close()
                            return [None, file_path]
                        elif resp.status == 501:
                            return ['Wolfram cannot interpret your request.', None]
                        else:
                            return ['[!] Wolfram Server Status {}'.format(resp.status), None]

        banner = Embed(title='Wolfram Help', description=fetch_file('help', 'wolfram'))
        return banner
    except Exception as e:
        if VERBOSE >= 0:
            print('[!] Wolfram failed to process command on: {}'.format(message.content))
            print('[!] {}'.format(e))
        return None


async def get_todays_word(message):
    """
	Pull the word of the day from www.wordsmith.org
	:param message: <Discord.message object> 
	:return: <str> Banner
	"""
    increment_usage(message.guild, 'wotd')

    async with aiohttp.ClientSession() as session:
        async with session.get(URL_WOTD) as resp:
            if resp.status == 200:
                text = await resp.read()
            else:
                if VERBOSE >= 2:
                    print("[!] Status {}".format(resp.status))

    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()
    text = text.split('with Anu Garg')
    text = text[1].split('A THOUGHT FOR TODAY')
    text = text[0].strip()
    text = text.split('\n')

    fields = {'header': '', }
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


def get_help(message):
    """
	Return the help file located in ./docs/help
	:param message: <Discord.message object>
	:return: <String> The local help file
	"""
    increment_usage(message.guild, 'help')
    return wrap(fetch_file('help', 'dict'), 1990)
