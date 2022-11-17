# TODO pull raw lists then convert to render for messaging
# so that filters can be combined DRY
# TODO atomize movie queue for preservation when q ends
# TODO add command to see queue
# TODO add skip vote command
# TODO add shuffle / sort queue command
# TODO page-ize long results
# TODO list most recently added

import configparser
# import os
import random
# import secrets
# import subprocess
# from multiprocessing import Process
import re

import discord
from plexapi.myplex import MyPlexAccount

from tutil import wrap, debug
from constants import DEFAULT_DIR, DIVIDER

# Read in config
config = configparser.ConfigParser()
config.read(DEFAULT_DIR + '/config.ini')
# os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Connect to plex server
account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect()
# Global variables to handle state
# videoPlaying = False
# ffmpegID = 0
# Define discord client
intents = discord.Intents.default()
# TODO remove unneeded
intents.messages = True
intents.voice_states = True
intents.presences = True
intents.guild_messages = True
intents.message_content = True
client = discord.Client(intents=intents)
#regex_is_digit = '^[0-9]+$'

# global videoPlaying
# global ffmpegID
global plexClient

@debug
async def helper(message: discord.Message, op_override=None):
    """
    Main entry point from main.py
    :param op_override: Activate a specific operator
    :param message: <Discord.message object>
    :return: <lambda function> Internal function dispatch
    """

    args = message.content.split()
    ops = {'search'}

    operator = 'help'
    if len(args) > 1 and args[1] in ops:
        operator = args[1]
    if op_override:
        operator = op_override

    return {
        'search': lambda: search_dispatch(args),
        'help': lambda: help(),
    }.get(operator, lambda: None)()



@debug
def search_dispatch(args):
    """
    Search the Plex instance.

    plex search libraries
    plex search (movie | tv | music) --option <argument>
    plex search (movie | tv | music) ([<title>] [<year>]) --option <argument>
    plex search (movie | tv | music) random
    plex search (movie | tv | music) collections
    plex search (movie | tv | music) unwatched
    plex search (movie | tv | music) recent
    plex search (movie | tv | music) inprogress

    Options:
      -h --help            Show this help prompt
      -a --all             List everything, overrides --limit
      -l --limit           Limit results to N elements [Default: 10]
      -t --title           Title of the media
      -y --year            Year of release
      -d --decade          Search for a specific decade (e.g. 2000)
      -A --actor           Search by actor name
      -D --director        Search by director name
      -g --genre           Search for a specific genre
      -al --audio          Search for a specific audio language (3 character code, e.g. jpn)
      -sl --sub            Search for a specific subtitle language (3 character code, e.g. eng)
      -cr --contentrating  Search for a specific content rating (e.g. PG-13, R)

    :param args:
    :return:
    """
    # Sanitize input
    # Some users will do --option=argument while some will do --option argument
    args = args.split('=')
    args = args.strip()
    # Add if statement to this to avoid -D becoming equivalent to -d, etc
    args = [arg.lower() for arg in args if not arg.startswith('-')]
    # TODO add Speller library

    regex_is_year = r"\d{4}"
    # Setup blanks
    options = {
        "library": None,
        "limit": 10,
        "title": None,
        "year": re.search(regex_is_year, ' '.join(args[1:2])), # None if no matches
        "decade": None,
        "actor": None,
        "director": None,
        "genre": None,
        "audio_language": None,
        "subtitle_language": None,
        "content_rating": None,
    }

    # Handle special options
    if {'-h', '--help'}.intersection(args):
        return get_search_help()
    if {'-a', '--all'}.intersection(args):
        options["limit"] = None
    if '-l' in args:
        options["limit"] = args[args.index('-l') + 1]
    elif '--limit' in args:
        options["limit"] = args[args.index('--limit') + 1]
    if '-y' in args:
        options["year"] = args[args.index('-y') + 1]
    elif '--year' in args:
        options["year"] = args[args.index('--year') + 1]
    if '-d' in args:
        options["decade"] = args[args.index('-d') + 1]
    elif '--decade' in args:
        options["decade"] = args[args.index('--decade') + 1]
    if '-A' in args:
        options["actor"] = args[args.index('-a') + 1]
        # Check if both first and last name were provided
        if not args[args.index(options["actor"]) + 1].startswith('-'):
            options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    elif '--actor' in args:
        options["actor"] = args[args.index('--actor') + 1]
        if not args[args.index(options["actor"]) + 1].startswith('-'):
            options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    if '-D' in args:
        options["director"] = args[args.index('-D') + 1]
        # Check if both first and last name were provided
        if not args[args.index(options["director"]) + 1].startswith('-'):
            options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    elif '--director' in args:
        options["director"] = args[args.index('--director') + 1]
        if not args[args.index(options["director"]) + 1].startswith('-'):
            options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    if '-g' in args:
        options["genre"] = args[args.index('-g') + 1]
    elif '--genre' in args:
        options["genre"] = args[args.index('--genre') + 1]
    if '-al' in args:
        options["audio_language"] = args[args.index('-al') + 1]
    elif '--audio' in args:
        options["audio_language"] = args[args.index('--audio') + 1]
    if '-sl' in args:
        options["subtitle_language"] = args[args.index('-sl') + 1]
    elif '--sub' in args:
        options["subtitle_language"] = args[args.index('--sub') + 1]
    if '-cr' in args:
        options["content_rating"] = args[args.index('-cr') + 1]
    elif '--sub' in args:
        options["content_rating"] = args[args.index('--contentrating') + 1]


    # Determine library
    # We require this of the user to prevent search results taking too long
    if args[0] in {'tv', 'television'}:
        library = 'TV'
    elif args[0] in {'movie', 'movies', 'film', 'films'}:
        library = 'Movies'
    elif args[0] in {'music'}:
        library = 'Music'
    else:
        return 'Please specify whether to search `movie`, `tv`, or `music`. ' \
               'See `plex search help` for more information.'

    # User entered simply "plex search"
    if not args[1]:
        return 'Please specify a search parameter. ' \
               'See `plex search help` for more information.'
    # Handle specific search cases
    if args[1] in {'library', 'libraries', 'lib', 'libs'}:
        return get_library_list()
    elif args[1] in {'random', 'rand'}:
        return get_random(library, options)
    elif args[1] in {'collection', 'collections'}:
        return get_collections_list(library)
    elif args[1] in {'unwatched'}:
        return get_unwatched(library, options)
    elif args[1] in {'inprogress'}:
        return get_in_progress(library, options)
    elif args[1] in {'recent', 'new'}:
        return get_recently_added(library, options)

    if not args[2]:
        return 'Additional search parameters required. ' \
               'See `plex search help` for more information.'
    # Handle generic search
    else:
        return search_library(library, options)

# TODO dummy method needs replacing
def get_library_list() -> list:
    """
    Get list of libraries available on the Plex instance
    :return:
    """
    return ['Movies', 'TV', 'Music']


def get_random(library: str, options: dict) -> list:
    """
    Get LIMIT [default: 10] number of random titles from LIBRARY
    :param library:
    :param limit:
    :return:
    """
    # replace search with search_library()
    result = plex.library.selection(library)
    return random.choices(result, options["limit"])


# TODO dummy method
def get_collections_list(library: str) -> list:
    """
    Get list of collections available in the library
    :param library:
    :return:
    """
    return None


# TODO implement limit
# try search()[:limit]
def get_unwatched(library: str, options: dict) -> list:
    """
    Get list of unplayed media in the library
    :param library:
    :param limit:
    :return:
    """
    # replace search with search_library()
    result = plex.library.section(library)
    return result.search(unwatched=True)


# TODO dummy method
def get_in_progress(library: str, options: dict) -> list:
    """
    Get list of media that has been partially played
    :param library:
    :param limit:
    :return:
    """
    return None


# TODO dummy method
def get_recently_added(library: str, options: dict) -> list:
    """
    Get list of most recently added media
    :param library:
    :param limit:
    :return:
    """
    return None


# TODO dummy method
def search_library(library: str, options: dict) -> list:
    """
    The main search function of the Plex instance
    :param library:
    :param options:
    :return:
    """
    # Determine which options were passed
    return None


def get_search_help() -> str:
    return """Search the Plex instance.

    plex search libraries
    plex search (movie | tv | music) --option <argument>
    plex search (movie | tv | music) ([<title>] [<year>]) --option <argument>
    plex search (movie | tv | music) random
    plex search (movie | tv | music) collections
    plex search (movie | tv | music) unwatched
    plex search (movie | tv | music) recent
    plex search (movie | tv | music) inprogress

    Options:
      -h --help            Show this help prompt
      -a --all             List everything, overrides --limit
      -l --limit           Limit results to N elements [Default: 10]
      -t --title           Title of the media
      -y --year            Year of release
      -d --decade          Search for a specific decade (e.g. 2000)
      -A --actor           Search by actor name
      -D --director        Search by director name
      -g --genre           Search for a specific genre
      -al --audio          Search for a specific audio language (3 character code, e.g. jpn)
      -sl --sub            Search for a specific subtitle language (3 character code, e.g. eng)
      -cr --contentrating  Search for a specific content rating (e.g. PG-13, R)
    """


#
# @debug
# def list_movies(args: list) -> list:
#     movies = plex.library.section('Movies')
#     msg = ''
#     if 'unwatched' in args:
#         for video in movies.search(unwatched=True):
#             msg = f'{msg}{video.title}\n'
#     elif 'random' in args:
#         choice = random.choice(movies.search())
#         msg = f'{choice.title} ({choice.year})'
#     else:
#         for video in movies.search():
#             msg = f'{msg}{video.title}\n'
#     return wrap(msg, 1999)
#
#
# @debug
# def list_movies_year(year: str) -> list:
#     """
#     List all movies released in a specified year.
#     :param year:
#     :return:
#     """
#     msg = 'No movie found'
#     movies = plex.library.section('Movies')
#     result = movies.all(year=year)
#     if len(result) > 0:
#         for video in result:
#             msg = f'**{year}**\r{DIVIDER}\r`{video.title}`\r'
#     return wrap(msg, 1999)
#
#
#
#
# @debug
# def search_movies(args: list) -> list:
#     # Define blank message
#     msg = 'No movie found'
#     year = None
#     name = ' '.join(args).strip()
#     # Check if specific year was requested to avoid remakes
#     year = re.findall(regex_is_year, args[-1])
#     # Get the name of the movie from the message
#     # Define the movie library
#     movies = plex.library.section('Movies')
#     if year:
#         name = ' '.join(args[:-1]).strip()
#         result = movies.search(name, year=year)
#     else:
#         result = movies.search(name)
#     if len(result) > 0:
#         # Loop through the search results and add them to the message
#         for video in result:
#             msg = f'{msg}`{video.title} - {video.year}`\r'
#     return wrap(msg, 1999)
#
#
# def search_tv(args):
#     # Define blank message
#     msg = ''
#     # Get the name of the video from the message
#     name = ' '.join(args[1])
#     # Define the tv library
#     tv = plex.library.section('TV Shows')
#     if len(tv.search(name)) > 0:
#         # Loop through the search results and add them to the message
#         for video in tv.search(name):
#             msg = msg + "```\r" + video.title
#             for season in video.seasons():
#                 msg = msg + "\rSeason " + str(season.index) + "\r"
#                 for episode in season.episodes():
#                     msg = msg + str(episode.index) + " "
#         msg = msg + '```'
#     else:
#         msg = 'No TV show found'
#     # Send message with search results
#     return wrap(msg, 1999)
#
#
# # TODO update to match when finished
# def help():
#     pass