# TODO add shuffle / sort queue command
# TODO page-ize long results
# TODO add play music / tv
# TODO break out resume / seek_to

import configparser
import random
import re
import time
from typing import Union

import discord
import plexapi.video
from plexapi.myplex import MyPlexAccount

from constants import DEFAULT_DIR, VERBOSE, BOT
from tutil import flatten_sublist, get_sec, is_admin
# from tutil import debug

config, account, plex, client_name, voice_channel_id = \
    configparser.ConfigParser, str, plexapi.myplex.PlexClient, str, int
# 'queue' and 'last' are a list of plexapi.Video.Movie
queue = []  # type: list[plexapi.video.Movie]
last = []  # type: list[Union[plexapi.video.Movie, str]]
# 'skip_votes' is a list of Discord Member ID's to ensure uniqueness
skip_votes = []  # type: list[discord.Member.id]
# Confirm we received a valid 4-length digit for --year search
regex_is_year = r"\d{4}"  # type: re


def setup() -> None:
    """
    Establish global variables, then connect to the Plex instance.
    :return:
    """
    global config, account, plex, client_name, voice_channel_id
    # Read in config
    config = configparser.ConfigParser()
    config.read(DEFAULT_DIR + '/config.ini')

    # Connect to Plex
    try:
        account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
        plex = account.resource(config['plex']['Server']).connect()
        voice_channel_id = int(config['discord']['VC_ID'])  # type: int
        client_name = config['plex']['Name']  # type: str
    except Exception as e:
        print(f'Oops! Something went wrong: {e}')
        print('Is the Plex instance online?')
    if VERBOSE >= 0:
        print('[+] End Plex Setup')


async def helper(message: discord.Message, op_override=None):
    """
    Main entry point from main.py
    :param op_override: Activate a specific operator
    :param message: <Discord.message object>
    :return: <lambda function> Internal function dispatch
    """
    args = message.content.split()
    ops = {'search',
           'help',
           'play',
           'next',
           'clients',
           'add',
           'clear',
           'pause',
           'resume',
           'queue',
           # 'play music'
           }

    # If the user calls simple "$plex" with no options, return the help statement
    operator = 'help'
    if len(args) > 1 and args[1] in ops:
        operator = args[1]
    # 'op_override' exists for testing purposes, it should never be possible for a user to declare it from Discord
    if op_override:
        operator = op_override

    # lambda functions cannot be awaited
    # we must await 'next_queue' as it calls 'async tutil.is_admin()'
    if operator == 'next':
        result = await next_queue(message)
    else:
        # Makeshift switch statement / condensed if-else
        result = {
            'search': lambda: search_dispatch(args),
            'help': lambda: get_help(),
            'clients': lambda: list_clients(),
            'add': lambda: add_to_queue(),
            'play': lambda: play_media(),
            'clear': lambda: clear_queue(args),
            'pause': lambda: pause_media(),
            'resume': lambda: resume_media(args),
            'queue': lambda: show_queue(),
        }.get(operator, lambda: None)()
    print(f'Result is: {result}')

    if operator == 'search':
        if not {'help', '-h', '--help'}.intersection(args):
            # TODO check if this even works
            last.clear()
            for each in result[0]:
                last.append(each)
            if not result:
                return 'Nothing found. Please see `$plex search -h` or `$plex help` for more information.'
        result = rendered(result)
    return result


def rendered(result: list) -> str:
    """
    Convert raw results to something Discord safe
    :param result:
    :return:
    """
    # We were given a result from a non-search function
    if len(result) == 1:
        return result[0]
    # We were given a result from a search function
    else:
        summary = result[2]
        result = result[0]
        banner = []
        for each in result:
            if type(each) == plexapi.video.Movie:
                duration = int(each.duration / 1000)
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                if summary:
                    banner.append(f'`{each.title} - ({each.year}) -- {h:02d}:{m:02d}:{s:02d}`\r --{each.summary}')
                else:
                    banner.append(f'`{each.title} - ({each.year}) -- {h:02d}:{m:02d}:{s:02d}`')
            else:
                banner.append(f'{each.title}')
        return '\r'.join(banner)


# TODO allow admins to establish which client to use if there are multiple.
def list_clients() -> str:
    """
    Helper function to get names of connected plexapi.Clients on network.
    This is for internal testing only.
    :return:
    """
    voice_channel = BOT.get_channel(voice_channel_id)
    print(voice_channel)
    print(voice_channel.members)
    for each in plex.clients():
        print(each)
    return '\r'.join(plex.clients())


def play_media() -> str:
    """
    Start the first item in queue.
    :return:
    """
    try:
        player = plex.client(client_name)
    except Exception as e:
        return f"Oops something went wrong! {e}\nIs the Plex instance online?"
    if len(queue) > 0:
        movie = plex.library.section('Movies').get(queue[0].title)
        player.playMedia(media=movie)
        return f'Now playing: {movie.title}'
    else:
        return "No media in queue."


def pause_media() -> str:
    """
    Pause anything currently playing.
    :return:
    """
    try:
        player = plex.client(client_name)
        player.pause()
        return "Paused. Use `$plex resume hh:mm:ss` to start again."
    except Exception as e:
        return f"Oops something went wrong! {e}"


def resume_media(args: list) -> str:
    """
    Skip to given hh:mm:ss of current media.
    :param args:
    :return:
    """
    ms = get_sec(args[2]) * 1000
    try:
        result = play_media()
        # We need to sleep() because if we call player.seekTo() too soon it will be ignored if movie is still loading.
        # A value between 2-4 seconds seems to work best.
        time.sleep(3)
        plex.client(client_name).seekTo(ms)
        return f'{result} at {args[2]}'
    except Exception as e:
        return f"Oops something went wrong! {e}"


def show_queue() -> str:
    """
    Show what is currently contained in 'queue'
    :return:
    """
    return '\r'.join([f'{_.title} - ({_.year})' for _ in queue])


def clear_queue(args: list) -> str:
    """
    Remove everything in queue.
    :return:
    """
    if {'q', 'queue'}.intersection(args):
        if len(queue):
            skip_votes.clear()
            queue.clear()
            return "Cleared queue."
        else:
            return "There is already nothing in queue."
    elif {'vote', 'votes', 'skip'}.intersection(args):
        skip_votes.clear()
        return "Cleared all votes to skip."
    else:
        return "Please specify either `votes` or `queue`."


async def next_queue(message: discord.Message) -> str:
    """
    Remove first item in queue and start the second item.
    Based on a simple majority vote of users in the config['discord']['VC_ID'] channel.
    Users with admin / mod roles can always skip.
    :param message: <Discord.message object>
    :return:
    """
    if len(queue):
        voice_channel = BOT.get_channel(voice_channel_id)  # type: discord.VoiceChannel
        if await is_admin(message.author, message) or len(skip_votes) > int(len(voice_channel.members) / 2):
            queue.pop(0)
            skip_votes.clear()
            return play_media()
        else:
            if message.author.id not in skip_votes:
                skip_votes.append(message.author.id)
                return f"Added vote to skip. {len(skip_votes)}/{len(voice_channel.members)}"
            else:
                return f"You have already voted {message.author.name}.\n" \
                       f"All votes can be cleared with `$plex clear votes`."
    else:
        return "There is already nothing in queue."


def add_to_queue() -> str:
    """
    Add the results of the most recent search to the play queue.
    :return:
    """
    if not last:
        return "Nothing to add. Use `$plex search` first."
    else:
        banner = ["Added the following to play queue: "]
        for each in last:
            queue.append(each)
            banner.append(each.title)
        return '\r'.join(banner)


def parse_options(args: list, options: dict) -> dict:
    """
    Check with --options were specified and convert them to dictionary values for library search.
    :param args:
    :param options:
    :return:
    """
    # similar = False
    # summary = False
    # Handle special options
    # TODO is --all needed?
    # all
    if {'-a', '--all'}.intersection(args):
        options["limit"] = None
    # title
    if '-t' in args:
        start = args[args.index('-t') + 1]
        options["title"] = start
        for _ in args[args.index(start) + 1:]:
            if _.startswith('-'):
                break
            else:
                options["title"] = f'{start} {_}'
    elif '--title' in args:
        start = args[args.index('--title') + 1]
        options["title"] = start
        for _ in args[args.index(start) + 1:]:
            if _.startswith('-'):
                break
            else:
                options["title"] = f'{start} {_}'
    # limit
    if '-l' in args:
        options["limit"] = int(args[args.index('-l') + 1])
    elif '--limit' in args:
        options["limit"] = int(args[args.index('--limit') + 1])
    # year
    if '-y' in args:
        options["year"] = args[args.index('-y') + 1]
    elif '--year' in args:
        options["year"] = args[args.index('--year') + 1]
    # decade
    if '-d' in args:
        options["decade"] = args[args.index('-d') + 1]
    elif '--decade' in args:
        options["decade"] = args[args.index('--decade') + 1]
    # TODO test this works with 3+ part names
    # actor
    if '-A' in args:
        start = args[args.index('-A') + 1]
        options["actor"] = start
        for _ in args[args.index(start) + 1:]:
            if _.startswith('-'):
                break
            else:
                options["actor"] = f'{start} {_}'
        # options["actor"] = args[args.index('-a') + 1]
        # # Check if BOTh first and last name were provided
        # if not args[args.index(options["actor"]) + 1].startswith('-'):
        #     options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    elif '--actor' in args:
        start = args[args.index('-A') + 1]
        options["actor"] = start
        for _ in args[args.index(start) + 1:]:
            if _.startswith('-'):
                break
            else:
                options["actor"] = f'{start} {_}'
        # options["actor"] = args[args.index('--actor') + 1]
        # if not args[args.index(options["actor"]) + 1].startswith('-'):
        #     options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    # director
    if '-D' in args:
        options["director"] = args[args.index('-D') + 1]
        # Check if BOTh first and last name were provided
        if not args[args.index(options["director"]) + 1].startswith('-'):
            options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    elif '--director' in args:
        options["director"] = args[args.index('--director') + 1]
        if not args[args.index(options["director"]) + 1].startswith('-'):
            options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    # library section
    if '-L' in args:
        options["library"] = args[args.index('-L') + 1]
    elif '--library' in args:
        options["library"] = args[args.index('--library') + 1]
    # unwatched
    if '-U' in args:
        options["unwatched"] = True
    elif '--unwatched' in args:
        options["unwatched"] = True
    # genre
    if '-g' in args:
        options["genre"] = args[args.index('-g') + 1]
    elif '--genre' in args:
        options["genre"] = args[args.index('--genre') + 1]
    # audio language
    if '-al' in args:
        options["audio_language"] = args[args.index('-al') + 1]
    elif '--audio' in args:
        options["audio_language"] = args[args.index('--audio') + 1]
    # subtitle language
    if '-sl' in args:
        options["subtitle_language"] = args[args.index('-sl') + 1]
    elif '--sub' in args:
        options["subtitle_language"] = args[args.index('--sub') + 1]
    # content rating
    if '-cr' in args:
        options["content_rating"] = args[args.index('-cr') + 1]
    elif '--contentrating' in args:
        options["content_rating"] = args[args.index('--contentrating') + 1]
    # TODO similar / summary search currently unimplemented
    # if '-sim' in args:
    #     similar = True
    # elif '--similar' in args:
    #     similar = True
    # if '-sum' in args:
    #     summary = True
    # elif '--summary' in args:
    #     summary = True
    return options


def search_dispatch(args):
    """
    Search the Plex instance.
    :param args:
    :return:
    """
    # Sanitize input
    # Some users will do --option=argument while some will do --option argument
    try:
        args = [arg.split('=') for arg in args]
        args = flatten_sublist(args)
    # TODO over broad exception, can we even break anything here? is this needed?
    except Exception as e:
        print(e)
        pass
    # Add if statement to this to avoid -D becoming equivalent to -d, etc
    args = [arg.lower().strip() if not arg.startswith('-') else arg for arg in args]
    # TODO add Speller library
    args = args[2:]
    if VERBOSE >= 2:
        print(f'args are: {args}')

    # Setup blanks for Plex Advanced Filters
    options = {
        "library": None,
        "limit": None,
        "title": None,
        "year": re.search(regex_is_year, ' '.join(args[1:2])),  # None if no matches
        "decade": None,
        "actor": None,
        "director": None,
        "genre": None,
        "audio_language": None,
        "subtitle_language": None,
        "content_rating": None,
        "unwatched": None,
    }
    result = None
    if VERBOSE >= 2:
        print(f'options set: {options}')

    # check if no parameters were passed
    basic_search = True
    for each in args:
        if each.startswith('-'):
            basic_search = False
            break
    if basic_search:
        options["title"] = ' '.join(args)

    # help
    if {'-h', '--help'}.intersection(args):
        return [get_search_help()]
    else:
        options = parse_options(args, options)
        if not options["limit"]:
            options["limit"] = 10
        if VERBOSE >= 2:
            print(f'parameters set: {options}')
        # User entered simply "plex search"
        if not args[0]:
            result = ['Please specify a search parameter.\nSee `plex search help` for more information.']

        # Determine library
        # We require this of the user to prevent search results taking too long
        if args[0] in {'library', 'libraries', 'lib', 'libs'}:
            return [get_library_list()]
        elif {args[0], options["library"]}.intersection({'movie', 'movies', 'film', 'films'}):
            options["library"] = 'Movies'
        elif {args[0], options["library"]}.intersection({'music', 'songs'}):
            options["library"] = 'Music'
        elif {args[0], options["library"]}.intersection({'tv', 'television', 'tv shows', 'shows'}):
            options["library"] = 'TV Shows'
        else:
            if not options["library"]:
                options["library"] = 'Movies'

        # Handle specific search cases
        if args[0] in {'random', 'rand'}:
            result = get_random(options)
        elif args[0] in {'collection', 'collections'}:
            result = get_collections_list(options)
        elif args[0] in {'inprogress'}:
            result = get_in_progress(options)
        elif args[0] in {'recent', 'new'}:
            result = get_recently_added(options)

        # Generic search
        if not result:
            result = search_library(options)
        # 'False' values are placeholders for future implementation of 'similar' and 'summary' searches.
        # Currently, need to keep them to indicate to 'rendered()' we are returning search results.
        return [result, False, False]


def search_library(options: dict) -> list:
    """
    The main search function of the Plex instance
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    try:
        # TODO implement 'or' and 'not'
        # Why are you using camelCase and not following PEP8 guidelines?
        #
        # This API reads XML documents provided by MyPlex and the Plex Server.
        # We decided to conform to their style so that the API variable names directly match with
        # the provided XML documents.
        # noinspection PyPep8Naming
        advancedFilters = {
            'and': [
                {'year': options["year"]},
                {'title': options["title"]},
                {'decade': options["decade"]},
                {'actor': options["actor"]},
                {'director': options["director"]},
                {'genre': options["genre"]},
                {'audioLanguage': options["audio_language"]},
                {'subtitleLanguage': options["subtitle_language"]},
                {'contentRating': options["content_rating"]},
                {'unwatched': options["unwatched"]}
            ]
        }
        # drop none values
        filtered = {}
        for each in advancedFilters["and"]:
            for k, v in each.items():
                if v:
                    filtered[k] = v
        advancedFilters["and"] = [filtered]
        selection = selection.search(filters=advancedFilters)
        if options["limit"] is None:
            options["limit"] = 10
    except Exception as e:
        print(f'Oops! Something went wrong during Advanced Filter selection.\n'
              f'Trying to fall back to default title search.\n{e}')
        try:
            selection = selection.search(options["title"])
        except Exception as e:
            return [f'Oops! Something went wrong. Please check your search and try again.\n{e}']
    return list(set(random.choices(selection, k=options["limit"])))


def get_library_list() -> str:
    """
    Get list of libraries available on the Plex instance
    :return:
    """
    return '\r'.join([section.title for section in plex.library.sections()])


def get_random(options: dict) -> list:
    """
    Get LIMIT [default: 10] number of random titles from LIBRARY
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.search()
    if options["limit"] is None:
        options["limit"] = 10
    return [*set(random.choices(selection, k=options["limit"]))]


def get_collections_list(options: dict) -> list:
    """
    Get list of collections available in the library
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.collections()
    return [*set(random.choices(selection, k=options["limit"]))]


# TODO convert to parameter -ip --inprogress
def get_in_progress(options: dict) -> list:
    """
    Get list of media that has been partially played
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.search(filters={"inProgress": True})
    if not len(selection):
        return ['No media in progress.']
    return [*set(random.choices(selection, k=options["limit"]))]


def get_recently_added(options: dict) -> list:
    """
    Get list of most recently added media
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.recentlyAdded()
    return [*set(random.choices(selection, k=options["limit"]))]


def get_help() -> str:
    """
    Return help file for usage.
    :return:
    """
    return """
    ```
    Control the Plex instance.

    plex search libraries
    plex search <library> -option <argument>
    plex add
    plex play
    plex pause
    plex resume <hh:mm:ss>
    plex next
    plex clear

    See plex search -h for more information about searching.
    To start a movie(s) first use plex search, then plex add to queue up the most recent search results.
    plex play will then start the queue.

    There is currently no way to un-pause a movie, so, take note of what time it was stopped at, then,
    use plex resume hh:mm:ss where h is hours, m is minutes, and s is seconds (e.g. 00:30:00 will start the
    movie at 30 minutes in). You must provide zeros as needed (e.g. do NOT do :30: or 30 for thirty minutes).
    ```
    """


# TODO update to reflect current state
def get_search_help() -> str:
    """
    Return help file for usage of search command.
    :return:
    """
    return """
    ```
    Search the Plex instance.

    plex search libraries
    plex search <library> -option <argument>
    plex search <library> --option=<argument>
    plex search <library> ([<title>] [<year>]) --option <argument>
    plex search <library> random
    plex search <library> collections
    plex search <library> recent
    plex search <library> inprogress

    Options:
      library              Which library section to search [Default: Movies]
      -h --help            Show this help prompt
      -a --all             List everything, overrides --limit
      -l --limit           Limit results to N elements [Default: 10]
      -t --title           Title of the media
      -y --year            Year of release
      -d --decade          Search for a specific decade (e.g. 2000)
      -A --actor           Search by actor name
      -D --director        Search by director name
      -U --unwatched       Search for unplayed media.
      -g --genre           Search for a specific genre
      -al --audio          Search for a specific audio language (3 character code, e.g. jpn)
      -sl --sub            Search for a specific subtitle language (3 character code, e.g. eng)
      -cr --contentrating  Search for a specific content rating (e.g. PG-13, R)
    ```
    """


setup()

# def play_music() -> str:
#     """
#     Start the first item in queue.
#     :return:
#     """
#     try:
#         player = plex.client(client_name)
#     except Exception as e:
#         print(e)
#         return f"Oops something went wrong! {e}"
#     if len(queue) > 0:
#         movie = plex.library.section('Music').get(queue[0].title)
#         player.playMedia(media=movie)
#         return f'Now playing: {movie.title}'
#     else:
#         return "No media in queue."
