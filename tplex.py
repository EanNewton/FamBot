# TODO pull raw lists then convert to render for messaging
# so that filters can be combined DRY
# TODO atomize movie queue for preservation when q ends
# TODO add command to see queue
# TODO add skip vote command
# TODO add shuffle / sort queue command
# TODO page-ize long results

import configparser
import random
import re
import datetime

import discord
import plexapi.video
from plexapi.myplex import MyPlexAccount
from plexapi import playqueue, exceptions, client

from tutil import wrap, debug, flatten_sublist
from constants import DEFAULT_DIR, DIVIDER

# Read in config
config = configparser.ConfigParser()
config.read(DEFAULT_DIR + '/config.ini')
# Connect to plex server
account = MyPlexAccount(config['plex']['Username'], config['plex']['Password'])
plex = account.resource(config['plex']['Server']).connect()
regex_is_year = r"\d{4}"
queue = []


@debug
async def helper(message: discord.Message, op_override=None):
    """
    Main entry point from main.py
    :param op_override: Activate a specific operator
    :param message: <Discord.message object>
    :return: <lambda function> Internal function dispatch
    """

    args = message.content.split()
    ops = {'search', 'help', 'play'}

    operator = 'help'
    if len(args) > 1 and args[1] in ops:
        operator = args[1]
    if op_override:
        operator = op_override

    result = {
        'search': lambda: search_dispatch(args),
        'help': lambda: get_help(),
    }.get(operator, lambda: None)()
    if not result:
        return 'Nothing found. Please see `$plex search -h` or `$plex help` for more information.'
    result = rendered(result)
    return result


@debug
def rendered(result: list) -> list:
    """
    Convert raw results to something Discord safe
    :param result:
    :return:
    """
    summary = result[2]
    similar = result[1]
    result = result[0]
    print(result, similar)
    rendered = []
    if similar:
        return 'This feature is currently under development.'
        for each in result:
            print(each)
            rendered.append(f'\r**{each.title}**')
            rendered.append(f'{each.similar.title}')
    else:
        for each in result:
            print(each)
            if type(each) == plexapi.video.Movie:
                duration = int(each.duration / 1000)
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                if summary:
                    rendered.append(f'`{each.title} - ({each.year}) -- {h:02d}:{m:02d}:{s:02d}`\r --{each.summary}')
                else:
                    rendered.append(f'`{each.title} - ({each.year}) -- {h:02d}:{m:02d}:{s:02d}`')
    return rendered


@debug
def search_dispatch(args):
    """
    Search the Plex instance.

    plex search libraries
    plex search <library> --option <argument>
    plex search <library> ([<title>] [<year>]) --option <argument>
    plex search <library> random
    plex search <library> collections
    plex search <library> recent
    plex search <library> inprogress

    Options:
      -h --help            Show this help prompt
      -a --all             List everything, overrides --limit
      -l --limit           Limit results to N elements [Default: 10]
      -t --title           Title of the media
      -y --year            Year of release
      -d --decade          Search for a specific decade (e.g. 2000)
      -L --library         Specify which library section to search [Default: Movies]
      -A --actor           Search by actor name
      -D --director        Search by director name
      -U  --unwatched      Filter by unwatched
      -g --genre           Search for a specific genre
      -al --audio          Search for a specific audio language (3 character code, e.g. jpn)
      -sl --sub            Search for a specific subtitle language (3 character code, e.g. eng)
      -cr --contentrating  Search for a specific content rating (e.g. PG-13, R)
      -sim --similar       Find movies similar to given movie
      -sum --summary       Display a brief summary of the media

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
    # args = args.strip()
    # Add if statement to this to avoid -D becoming equivalent to -d, etc
    args = [arg.lower().strip() if not arg.startswith('-') else arg for arg in args]
    # TODO add Speller library
    args = args[2:]
    print(f'args are: {args}')

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
    similar = False
    summary = False
    print(f'options set: {options}')

    # check if no parameters were passed
    basic_search = True
    for each in args:
        if each.startswith('-'):
            basic_search = False
            break
    if basic_search:
        options["title"] = ' '.join(args)

    # Handle special options
    # help
    if {'-h', '--help'}.intersection(args):
        return get_search_help()
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
    print(f'parameters set: {options}')

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
    print(f'library determined: {options["library"]}')

    if args[0] in {'random', 'rand'}:
        result = get_random(options)
    elif args[0] in {'collection', 'collections'}:
        result = get_collections_list(options)
    # elif args[0] in {'unwatched'}:
    #     result = get_unwatched(options)
    elif args[0] in {'inprogress'}:
        result = get_in_progress(options)
    elif args[0] in {'recent', 'new'}:
        result = get_recently_added(options)

    # print('sim check')

    # elif '-sim' in args :
    #     similar = True
    print(f'special searches passed')

    # Generic search
    if not result:
        result = search_library(options)
    return [result, similar, summary]


@debug
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
            print(k, v)
            if v:
                filtered[k] = v
    # advancedFilters["or"] = [k: v for k, v in advancedFilters["or"].items() if v is not None]
    advancedFilters["and"] = [filtered]
    print(f'Advanced Filters: {advancedFilters}')
    try:
        selection = selection.search(filters=advancedFilters)
    except:
        print('advanced filters failed')
    print(f' Selection: {selection}')
    result = []
    choices = []
    if options["limit"] is None:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    # print(result)
    # for each in result:
    #     choices.append(f'{each.title} ({each.year})')
    #  print(f'\n---\n{choices}')
    result = list(set(result))
    # Breaks if not enough movies match
    # while len(result) < options["limit"]:
    #     choice = random.choice(selection)
    #     result.append(f'{choice.title} ({choice.year})')
    #     result = list(set(result))
    #return wrap('\r'.join(result), 1999)
    return result


def get_library_list() -> list:
    """
    Get list of libraries available on the Plex instance
    :return:
    """
    result = [section.title for section in plex.library.sections()]
    # TODO update to embed
    return '\r'.join(result)


def get_random(options: dict) -> list:
    """
    Get LIMIT [default: 10] number of random titles from LIBRARY
    :param options:
    :return:
    """
    # replace search with search_library()
    selection = plex.library.section(options["library"])
    selection = selection.search()
    result = []
    if options["limit"] is None:
        options["limit"] = 10
    # TODO janky method to prevent repitition
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    result = list(set(result))
    # while len(result) < options["limit"]:
    #     choice = random.choice(selection)
    #     result.append(f'{choice.title} ({choice.year})')
    #     result = list(set(result))
    # TODO update to embed
    return wrap('\r'.join(result), 1999)


def get_collections_list(options: dict) -> list:
    """
    Get list of collections available in the library
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = [_.title for _ in selection.collections()]
    result = []
    # result = [_.title for _ in result.collections]
    if not options["limit"]:
        options["limit"] = 10

    # TODO janky method to prevent repitition
    while len(result) < options["limit"]:
        result.append(random.choice(selection))
        result = list(set(result))
    # result = random.choices(result, k=options["limit"])
    # TODO convert to embed
    return wrap('\r'.join(result), 1999)


# TODO convert to parameter -U --unwatched
def get_unwatched(options: dict) -> list:
    """
    Get list of unplayed media in the library
    :param options:
    :return:
    """
    # replace search with search_library()
    selection = plex.library.section(options["library"])
    selection = selection.search(unwatched=True)
    result = []
    if not options["limit"]:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    result = list(set(result))
    # while len(result) < options["limit"]:
    #     choice = random.choice(selection)
    #     result.append(f'{choice.title} ({choice.year})')
    #     result = list(set(result))
    return result


# TODO convert to parameter -ip --inprogress
def get_in_progress(options: dict) -> list:
    """
    Get list of media that has been partially played
    :param options:
    :return:
    """
    selection = plex.library.section(options["library"])
    selection = selection.search(filters={"episode.inProgress": True})
    print(selection)
    if not len(selection):
        return 'No media in progress.'
    result = []
    if not options["limit"]:
        options["limit"] = 10
    result = random.choices(selection, k=options["limit"])
    for each in result:
        each = f'{each.title} ({each.year})'
    result = list(set(result))
    # while len(result) < options["limit"]:
    #     choice = random.choice(selection)
    #     result.append(choice.title)
    #     result = list(set(result))
    return result

@debug
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
    result = list(set(result))
    # while len(result) < options["limit"]:
    #     choice = random.choice(selection)
    #     result.append(f'{choice.title} ({choice.year})')
    #     result = list(set(result))
    return result


def get_search_help() -> str:
    """
    Return help file for usage
    :return:
    """
    return """
    ```
    Search the Plex instance.

    plex search libraries
    plex search <library> --option <argument>
    plex search <library> ([<title>] [<year>]) --option <argument>
    plex search <library> random
    plex search <library> collections
    plex search <library> unwatched
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
      -g --genre           Search for a specific genre
      -al --audio          Search for a specific audio language (3 character code, e.g. jpn)
      -sl --sub            Search for a specific subtitle language (3 character code, e.g. eng)
      -cr --contentrating  Search for a specific content rating (e.g. PG-13, R)
    ```
    """

# TODO update to match when finished
def get_help():
    pass

# play
# @bot.command()
# async def play(ctx, *item):
#     global queue
#     item = ' '.join(item)
#     movies = plex.library.section('Movies')
#     try:
#         def check(m):
#             return m.author == ctx.message.author and m.channel == ctx.channel
#
#         x = movies.search(item)
#         x.sort(reverse=True, key=lambda a: simbet(a.title, item))
#         if not x:
#             return
#         y = []
#         for l in x:
#             y.append(l.title)
#         if item == x[0].title:
#             movie = x[0]
#         else:
#             o = await ctx.send(f"Did you mean **{x[0].title}**?? yes/no")
#             try:
#                 msg = await bot.wait_for("message", check=check, timeout=10)
#                 if msg.content.lower() == 'yes':
#                     movie = x[0]
#                 else:
#                     return
#             except:
#                 await o.reply("Timed out")
#                 return
#         await ctx.message.reply("Playing `" + movie.title + '`')
#
#         if not queue:
#             queue = plexapi.playqueue.PlayQueue.create(plex, movie)
#             client.playMedia(queue)
#             await ctx.message.reply("Playing `" + item + '`')
#         else:
#             queue.addItem(movie)
#             client.refreshPlayQueue(queue)
#             await ctx.message.reply("Added to queue!")
#     except plexapi.exceptions.NotFound:
#         await ctx.message.reply("Movie not found!")# play



# @bot.command()
# async def play(ctx, *item):
#     global queue
#     item = ' '.join(item)
#     movies = plex.library.section('Movies')
#     try:
#         def check(m):
#             return m.author == ctx.message.author and m.channel == ctx.channel
#
#         x = movies.search(item)
#         x.sort(reverse=True, key=lambda a: simbet(a.title, item))
#         if not x:
#             return
#         y = []
#         for l in x:
#             y.append(l.title)
#         if item == x[0].title:
#             movie = x[0]
#         else:
#             o = await ctx.send(f"Did you mean **{x[0].title}**?? yes/no")
#             try:
#                 msg = await bot.wait_for("message", check=check, timeout=10)
#                 if msg.content.lower() == 'yes':
#                     movie = x[0]
#                 else:
#                     return
#             except:
#                 await o.reply("Timed out")
#                 return
#         await ctx.message.reply("Playing `" + movie.title + '`')
#
#         if not queue:
#             queue = plexapi.playqueue.PlayQueue.create(plex, movie)
#             client.playMedia(queue)
#             await ctx.message.reply("Playing `" + item + '`')
#         else:
#             queue.addItem(movie)
#             client.refreshPlayQueue(queue)
#             await ctx.message.reply("Added to queue!")
#     except plexapi.exceptions.NotFound:
#         await ctx.message.reply("Movie not found!")


