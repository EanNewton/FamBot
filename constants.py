#!/usr/bin/python3

from os import path, getenv
from dotenv import load_dotenv
from sqlalchemy import create_engine
from googletrans.constants import LANGCODES
from nltk.data import find as nltk_find
from nltk import download as nltk_download

try:
    nltk_find('stopwords')
except LookupError:
    nltk_download('stopwords')
finally:
    from nltk.corpus import stopwords

##################
# File Locations #
##################
DEFAULT_DIR = path.dirname(path.abspath(__file__))
PATH_DB = path.join(path.dirname(__file__), './log/quotes.db')
PATH_WOTD = path.join(path.dirname(__file__), './docs/wordoftheday.txt')
ENGINE = create_engine('sqlite:///./log/quotes.db', echo=False)

##################
# Bot & API Info #
##################
load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')
POC_TOKEN = getenv('POC_TOKEN')
GUILD = getenv('DISCORD_GUILD')
WOLFRAM = getenv('WOLFRAM_TOKEN')
VERSION = '06.19.2021'
VERBOSE = 1

#################################
# Internal Function Static Data #
#################################
# combine all 2 letter codes and fully qualified names into flat list from a dict()
LANGCODES = [each for tuple_ in LANGCODES.items() for each in tuple_]
DIVIDER = '<<>><<>><<>><<>><<>><<>><<>><<>><<>>\n'
URL_WOTD = 'https://www.wordsmith.org/words/today.html'
URL_WOLF_IMG = 'http://api.wolframalpha.com/v1/simple?appid={}&i={}'
URL_WOLF_TXT = 'http://api.wolframalpha.com/v1/result?appid={}&i={}'

URL_KEYWORDS = {
    'USAGE:': '**USAGE:**',
    'MEANING:': '**MEANING:**',
    'PRONUNCIATION:': '**PRONUNCIATION:**',
    'ETYMOLOGY:': '**ETYMOLOGY:**',
    'NOTES:': '**NOTES:**'
}

extSet = {
    'image': [
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'
    ],
    'audio': [
        '3gp', 'aa', 'aac', 'aax', 'act', 'aiff', 'alac', 'amr',
        'ape', 'au', 'awb', 'dct', 'dss', 'dvf', 'flac', 'gsm',
        'iklax', 'ivs', 'm4a', 'm4b', 'm4p', 'mmf', 'mp3', 'mpc',
        'msv', 'nmf', 'nsf', 'ogg', 'oga', 'mogg', 'opus', 'ra',
        'rm', 'raw', 'rf64', 'sln', 'tta', 'voc', 'vox', 'wav',
        'wma', 'wv', 'webm', '8svx', 'cda'
    ],
    'video': [
        'webm', 'mkv', 'flv', 'vob', 'ogv', 'ogg', 'drc',
        'gifv', 'mng', 'avi', 'mts', 'm2ts', 'ts', 'mov', 'qt',
        'wmv', 'yuv', 'rm', 'rmvb', 'asf', 'amv', 'mp4', 'm4p',
        'm4v', 'mpg', 'mp2', 'mpeg', 'mpe', 'mpv', 'm4v', 'svi',
        '3gp', '3g2', 'mxf', 'roq', 'nsv', 'f4v', 'f4p', 'f4a', 'f4b'
    ],
    'document': [
        '0', '1st', '600', '602', 'abw', 'acl', 'afp', 'ami',
        'ans', 'ascaww', 'ccf', 'csv', 'cwk', 'dbk', 'dita', 'doc',
        'docm', 'docx', 'dotdotx', 'dwd', 'egt', 'epub', 'ezw',
        'fdx', 'ftm', 'ftx', 'gdoc', 'html', 'hwp', 'hwpml', 'log',
        'lwp', 'mbp', 'md', 'me', 'mcw', 'mobinb', 'nbp', 'neis',
        'odm', 'odoc', 'odt', 'osheet', 'ott', 'ommpages', 'pap',
        'pdax', 'pdf', 'quox', 'rtf', 'rpt', 'sdw', 'sestw',
        'sxw', 'tex', 'info', 'troff', 'txt', 'uof', 'uoml', 'viawpd',
        'wps', 'wpt', 'wrd', 'wrf', 'wri', 'xhtml', 'xht', 'xml', 'xps'
    ]
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
], [
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
    ['anonymous', 'Anonymous Mode'],
    ['timer_channel', 'Timer Channel ID'],
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
EIGHTBALL = [
    # Yes
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
    # Maybe
    'Reply hazy, try again.',
    'Ask again later.',
    'Better not tell you now.',
    'Cannot predict now.',
    'Concentrate and ask again.',
    # No
    'Don\'t count on it.',
    'My reply is no.',
    'My sources say no.',
    'Outlook not so good',
    'Very doubtful.'
]

STOPWORDS = set(stopwords.words("english")).union([
    "wa",
    "thi",
    "https",
    "tenor",
    "com",
    "lol'",
    "lol '",
    "gif",
    "gif'",
    "gif '",
    "it'",
    "it '",
    "quote'",
    "quote '",
    "youtu",
    "cdn",
    "discordapp",
    "youtu be",
    "twitch",
    "twitter",
    " https",
    "https ",
    "https:",
    "https:/",
    "https://",
    "twitch tv",
    "twitch.tv",
    "com attachments",
    "com/attachments",
    ".com/attachments",
    ".com/attachments/",
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
    'invite': 'https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot',
    'github': 'https://github.com/EanNewton/FamBot'

}

help_dict = {
    'main': '`!wiki PHRASE` get the wiktionary.org entry for a PHRASE',
    'alternative': '`!dict`\n`!dictionary`\n`!wiktionary`',
}
