# TODO add command to see queue
# TODO add skip vote command
# TODO add shuffle / sort queue command
# TODO page-ize long results

import configparser
import random
import re

import discord
import plexapi.video
from plexapi.myplex import MyPlexAccount

from constants import DEFAULT_DIR
from tutil import wrap, debug, flatten_sublist, get_sec

# Read in config
config = configparser.ConfigParser()
config.read(DEFAULT_DIR + '/config.ini')
# Connect to plex server
account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect()
client_name = config['plex']['Name']

regex_is_year = r"\d{4}"
queue = []
last = []


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
           'resume'}

    operator = 'help'
    if len(args) > 1 and args[1] in ops:
        operator = args[1]
    if op_override:
        operator = op_override

    result = {
        'search': lambda: search_dispatch(args),
        'help': lambda: get_help(),
        'next': lambda: next_queue(),
        'clients': lambda: list_clients(),
        'add': lambda: add_to_queue(),
        'play': lambda: play_media(),
        'clear': lambda: clear_queue(),
        'pause': lambda: pause_media(),
        'resume': lambda: resume_media(args),
    }.get(operator, lambda: None)()
    if operator == 'search':
        if not {'help', '-h', '--help'}.intersection(args):
            for each in result[0]:
                last.clear()
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
    if len(result) == 1:
        return result[0]
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
    return '\r'.join(banner)


def list_clients() -> str:
    """
    Helper function to get names of connected plexapi.Clients on network.
    :return:
    """
    print(plex)
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
        print(e)
        return f"Oops something went wrong! {e}"
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
        return "Paused. Use `$plex resume` to start again."
    except Exception as e:
        print(e)
        return f"Oops something went wrong! {e}"


def resume_media(args: list) -> str:
    """
    Skip to given hh:mm:ss of current media.
    :param args:
    :return:
    """
    try:
        ms = get_sec(args[2]) * 1000
    except Exception as e:
        print(e)
        return f"Oops something went wrong! {e}"
    try:
        player = plex.client(client_name)
        result = play_media()
        player.seekTo(ms)
        return f'{result} at {args[2]}'
    except Exception as e:
        print(e)
        return f"Oops something went wrong! {e}"


def clear_queue() -> str:
    """
    Remove everything in queue.
    :return:
    """
    if len(queue):
        queue.clear()
        return "Cleared queue."
    else:
        return "There is already nothing in queue."


def next_queue() -> str:
    """
    Remove first item in queue and start the second item.
    :return:
    """
    if len(queue):
        queue.pop(0)
        return play_media()
    else:
        return "There is already nothing in queue."


def add_to_queue() -> str:
    """
    Add the results of the most recent search to the play queue.
    :return:
    """
    banner = ["Added the following to play queue: "]
    if not last:
        return "Nothing to add. Use `$plex search` first."
    else:
        for each in last:
            queue.append(each)
            banner.append(each.title)
        return '\r'.join(banner)


def parse_options(args: list, options: dict) -> tuple:
    similar = False
    summary = False
    # Handle special options
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
    # TODO update to match title search style to handle 3+ part names
    # actor
    if '-A' in args:
        options["actor"] = args[args.index('-a') + 1]
        # Check if both first and last name were provided
        if not args[args.index(options["actor"]) + 1].startswith('-'):
            options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    elif '--actor' in args:
        options["actor"] = args[args.index('--actor') + 1]
        if not args[args.index(options["actor"]) + 1].startswith('-'):
            options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    # director
    if '-D' in args:
        options["director"] = args[args.index('-D') + 1]
        # Check if both first and last name were provided
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
    if '-sim' in args:
        similar = True
    elif '--similar' in args:
        similar = True
    if '-sum' in args:
        summary = True
    elif '--summary' in args:
        summary = True
    return (options, similar, summary)


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
    except:
        pass
    # Add if statement to this to avoid -D becoming equivalent to -d, etc
    args = [arg.lower().strip() if not arg.startswith('-') else arg for arg in args]
    # TODO add Speller library
    args = args[2:]
    # print(f'args are: {args}')

    # Setup blanks
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
    # print(f'options set: {options}')

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
        options, similar, summary = parse_options(args, options)
        # print(f'parameters set: {options}')
        # User entered simply "plex search"
        if not args[0]:
            result = ['Please specify a search parameter. ' \
                      'See `plex search help` for more information.']
        # Handle specific search cases
        if args[0] in {'library', 'libraries', 'lib', 'libs'}:
            result = get_library_list()
        # Determine library
        # We require this of the user to prevent search results taking too long
        elif {args[0], options["library"]}.intersection({
            'movie', 'movies', 'film', 'films'}):
            options["library"] = 'Movies'
        elif {args[0], options["library"]}.intersection({
            'music', 'songs'}):
            options["library"] = 'Music'
        elif {args[0], options["library"]}.intersection({
            'tv', 'television', 'tv shows', 'shows'}):
            options["library"] = 'TV Shows'
        else:
            if not options["library"]:
                options["library"] = 'Movies'
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
        return [result, similar, summary]


def search_library(options: dict) -> list:
    """
    The main search function of the Plex instance
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
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
    try:
        selection = selection.search(filters=advancedFilters)
    except Exception as e:
        print('advanced filters failed')
        return [f'Oops something went wrong! {e}']
    if options["limit"] is None:
        options["limit"] = 10
    return list(set(random.choices(selection, k=options["limit"])))


def get_library_list() -> list:
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
    result = []
    if options["limit"] is None:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    return wrap('\r'.join(list(set(result))), 1999)


def get_collections_list(options: dict) -> list:
    """
    Get list of collections available in the library
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = [_.title for _ in selection.collections()]
    result = []
    if not options["limit"]:
        options["limit"] = 10
    while len(result) < options["limit"]:
        result.append(random.choice(selection))
        result = list(set(result))
    return wrap('\r'.join(result), 1999)


# TODO convert to parameter -ip --inprogress
def get_in_progress(options: dict) -> list:
    """
    Get list of media that has been partially played
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.search(filters={"episode.inProgress": True})
    if not len(selection):
        return 'No media in progress.'
    result = []
    if not options["limit"]:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    return list(set(result))


def get_recently_added(options: dict) -> list:
    """
    Get list of most recently added media
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.recentlyAdded()
    result = []
    if not options["limit"]:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    return list(set(result))


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
