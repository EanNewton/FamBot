#!/usr/bin/python3

from os import path, getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine
from googletrans.constants import LANGCODES
from nltk.corpus import stopwords

##################
# File Locations #
##################
DEFAULT_DIR = path.dirname(path.abspath(__file__))
PATH_DB = path.join(path.dirname(__file__), './log/quotes.db')
PATH_WOTD = path.join(path.dirname(__file__), './docs/wordoftheday.txt')
ENGINE = create_engine('sqlite:///./log/quotes.db', echo = False)

##################
# Bot & API Info #
##################
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
POC_TOKEN = getenv('POC_TOKEN')
GUILD = getenv('DISCORD_GUILD')
WOLFRAM = getenv('WOLFRAM_TOKEN')
VERSION = '9.15.2020'


#################################
# Internal Function Static Data #
#################################
#combine all 2 letter codes and fully qualified names into flat list from a dict()
LANGCODES = [each for tuple_ in LANGCODES.items() for each in tuple_]
DIVIDER = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n' 
URL_WOTD = 'https://www.wordsmith.org/words/today.html'
#URL_POTD = 'https://www.poetryfoundation.org/poems/poem-of-the-day.html'
URL_POTD = 'https://poems.com/todays-poem/'
URL_WOLF_IMG = 'http://api.wolframalpha.com/v1/simple?appid={}&i={}'
URL_WOLF_TXT = 'http://api.wolframalpha.com/v1/result?appid={}&i={}'

URL_KEYWORDS = {
    'USAGE:': '**USAGE:**',
    'MEANING:': '**MEANING:**',
    'PRONUNCIATION:': '**PRONUNCIATION:**',
    'ETYMOLOGY:': '**ETYMOLOGY:**',
    'NOTES:': '**NOTES:**'
    }

jsonFormatter = [[
		['0=', 'Monday = '],
		['1=', 'Tuesday = '],
		['2=', 'Wednesday = '],
		['3=', 'Thursday = '],
		['4=', 'Friday = '],
		['5=', 'Saturday = '],
		['6=', 'Sunday = '],
		[',', ', '],
		[';', '; '],
	],[
		['id', 'Server ID'],
		['guild_name', 'Server Name'],
		['locale', 'Server Locale'],
		['schedule', 'Schedule'],
		['url', 'URL Footer'],
		['quote_format', 'Quote Format'],
		['qAdd_format', 'Quote Added Format'],
		['lore_format', 'Lore Format'],
		['filtered', 'Blacklisted Words'],
		['mod_roles', 'Moderator Roles'],
	]]

TZ_ABBRS = {
    'jst': 'Asia/Tokyo',
    'est': 'America/New_York',
    'pst': 'America/Los_Angeles',
    'hst': 'Pacific/Honolulu',
    'china': 'Asia/Shanghai',
    'hk': 'Asia/Hong_Kong',
    'utc': 'Europe/London',
    'aest': 'Australia/Sydney',
    'cst': 'America/Chicago',
    'ast': 'America/Puerto_Rico',
    'canada': 'America/Vancouver',
    'korea': 'Asia/Seoul',
    'nz': 'Pacific/Auckland',
    'nzdt': 'Pacific/Auckland',
    'india': 'Asia/Kolkata',
    'new york': 'America/New_York',
    'new-york': 'America/New_York',
    'ny': 'America/New_York',
    'nyc': 'America/New_York',
    'la': 'America/Los_Angeles',
    'los-angeles': 'America/Los_Angeles',
    'los angeles': 'America/Los_Angeles',
    }

'''
with open('./docs/locales/abbr.txt', 'r') as f:
	for line in f:
		(key, val) = line.split(',')
		val = val.strip('\n')
		tzAbbrs[key] = val
'''
EIGHTBALL = {
    #Yes
	'It is certain.', 
    'It is decidedly so.', 
    'Without a doubt.',
	'Yes -- definitely.', 
    'You may rely on it.', 
    'As I see it, yes.',
	'Most likely.', 
    'Outlook good.', 
    'Yes.', 
    'Signs point to yes.',
    #Maybe
	'Reply hazy, try again.', 
    'Ask again later.', 
	'Better not tell you now.', 
    'Cannot predict now.',
	'Concentrate and ask again.', 
    #No
    'Don\'t count on it.', 
	'My reply is no.', 
    'My sources say no.', 
    'Outlook not so good',
	'Very doubtful.'
}

STOPWORDS = set(stopwords.words("english")).union([
	"channel cannot", 
	"channel cannot used music", 
	"cannot used music command", 
	"cannot used", 
	"used music", 
	"music command", 
	"channel cannot used", 
	"cannot used music", 
	"used music command", 
	"channel cannot used music command",
	"quote",
    "gif",
    "www",
    "http",
    "https",
    "com",
    "youtube",
    "'",
    "\"",
    "`",
    "im",
    "I",
    "like",
    "watch",
    "get",
    "got",
    "override",
    "schedule",
    "sched",
    "cc",
    "discordapp",
    "discord",
    ])

PUNCTUATION = [
    ',',
    '.',
    '!',
    '?',
    '-',
    '_',
    '+',
    '=',
    '@',
    '#',
    '$',
    '%',
    '^',
    '&',
    '*',
    '`',
    '(',
    ')',
    '[',
    ']',
    '{',
    '}',
    '/',
    '\\',
    '\'',
    '<',
    '>',
    ';',
    ':',
    '~',
    '|',
]


#############
# Help Info #
#############
help_general = {
    'commands': '',
    'paypal': 'https://www.paypal.com/biz/fund?id=UHBZFEDYWW7LS',
    'patreon': 'https://www.patreon.com/tangerinebot',
    'invite': 'https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot',
    'github': 'https://github.com/EanNewton/FamBot'
    
}

help_dict = {
    'main': '`!wiki PHRASE` get the wiktionary.org entry for a PHRASE',
    'alternative': '`!dict`\n`!dictionary`\n`!wiktionary`',
}
