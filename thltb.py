# TODO pull raw lists then convert to render for messaging
# so that filters can be combined DRY
# TODO atomize movie queue for preservation when q ends
# TODO add command to see queue
# TODO add skip vote command
# TODO add shuffle / sort queue command
# TODO page-ize long results


import discord
from howlongtobeatpy import HowLongToBeat

from tutil import wrap, debug, flatten_sublist
from constants import DIVIDER

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
    ops = {'search', 'help'}

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
        return 'Nothing found. Please see `$hltb search -h` or `$hltb help` for more information.'
    result = rendered(result)
    return result


@debug
def rendered(message: list) -> str:
    """
    Convert raw results to something Discord safe

    id
    game_name
    game_alias
    game_type
    game_image_url
    game_web_link
    review_score
    profile_dev
    profile_platforms
    release_world
    similarity
    json_content
    main_story
    main_extra
    completionist
    all_style

    :param result:
    :return:
    """
    similar = message[1]
    message = message[0]
    result = []
    if not similar:
        for each in message:
            attrs = vars(each)
            result.append(f"**{attrs['game_name']}**")
            result.append(f"Game Image: {attrs['game_image_url']}")
            result.append(f"Web Link: {attrs['game_web_link']}")
            result.append(f"Review Score: {attrs['review_score']}")
            result.append(f"Developer: {attrs['profile_dev']}")
            result.append(f"Platforms: {attrs['profile_platforms']}")
            result.append(f"Release Date: {attrs['release_world']}")
            result.append(f"Similarity to your search: {attrs['similarity'] * 100:.2f}%")
            result.append(f"{DIVIDER.strip()}")
            result.append(f"Main Story: {attrs['main_story']}")
            result.append(f"Main Extra: {attrs['main_extra']}")
            result.append(f"Completionist: {attrs['completionist']}")
    else:
        result = message
    return '\r'.join(result)


@debug
def search_dispatch(args):
    """
    Search How Long To Beat dot com.

    hltb search <title>
    hltb search <option> <title>

    Options:
      -h --help            Show this help prompt
      -id                  Search by id

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
    # print(f'args are: {args}')

    # Setup blanks
    options = {
        "library": None,
        "limit": None,
        "title": None,
        # "year": re.search(regex_is_year, ' '.join(args[1:2])),  # None if no matches
        # "decade": None,
        # "actor": None,
        # "director": None,
        # "genre": None,
        # "audio_language": None,
        # "subtitle_language": None,
        # "content_rating": None,
        # "unwatched": None,
        "id": None
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
    if {'-id'}.intersection(args):
        options["id"] = int(args[args.index('-id') + 1])
    # # title
    # if '-t' in args:
    #     start = args[args.index('-t') + 1]
    #     options["title"] = start
    #     for _ in args[args.index(start) + 1:]:
    #         if _.startswith('-'):
    #             break
    #         else:
    #             options["title"] = f'{start} {_}'
    # elif '--title' in args:
    #     start = args[args.index('--title') + 1]
    #     options["title"] = start
    #     for _ in args[args.index(start) + 1:]:
    #         if _.startswith('-'):
    #             break
    #         else:
    #             options["title"] = f'{start} {_}'
    # # limit
    # if '-l' in args:
    #     options["limit"] = int(args[args.index('-l') + 1])
    # elif '--limit' in args:
    #     options["limit"] = int(args[args.index('--limit') + 1])
    # # year
    # if '-y' in args:
    #     options["year"] = args[args.index('-y') + 1]
    # elif '--year' in args:
    #     options["year"] = args[args.index('--year') + 1]
    # # decade
    # if '-d' in args:
    #     options["decade"] = args[args.index('-d') + 1]
    # elif '--decade' in args:
    #     options["decade"] = args[args.index('--decade') + 1]
    # # TODO update to match title search style to handle 3+ part names
    # # actor
    # if '-A' in args:
    #     options["actor"] = args[args.index('-a') + 1]
    #     # Check if both first and last name were provided
    #     if not args[args.index(options["actor"]) + 1].startswith('-'):
    #         options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    # elif '--actor' in args:
    #     options["actor"] = args[args.index('--actor') + 1]
    #     if not args[args.index(options["actor"]) + 1].startswith('-'):
    #         options["actor"] = f'{options["actor"]} {args[args.index(options["actor"]) + 1]}'
    # # director
    # if '-D' in args:
    #     options["director"] = args[args.index('-D') + 1]
    #     # Check if both first and last name were provided
    #     if not args[args.index(options["director"]) + 1].startswith('-'):
    #         options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    # elif '--director' in args:
    #     options["director"] = args[args.index('--director') + 1]
    #     if not args[args.index(options["director"]) + 1].startswith('-'):
    #         options["director"] = f'{options["director"]} {args[args.index(options["director"]) + 1]}'
    # # library section
    # if '-L' in args:
    #     options["library"] = args[args.index('-L') + 1]
    # elif '--library' in args:
    #     options["library"] = args[args.index('--library') + 1]
    # # unwatched
    # if '-U' in args:
    #     options["unwatched"] = True
    # elif '--unwatched' in args:
    #     options["unwatched"] = True
    # # genre
    # if '-g' in args:
    #     options["genre"] = args[args.index('-g') + 1]
    # elif '--genre' in args:
    #     options["genre"] = args[args.index('--genre') + 1]
    # # audio language
    # if '-al' in args:
    #     options["audio_language"] = args[args.index('-al') + 1]
    # elif '--audio' in args:
    #     options["audio_language"] = args[args.index('--audio') + 1]
    # # subtitle language
    # if '-sl' in args:
    #     options["subtitle_language"] = args[args.index('-sl') + 1]
    # elif '--sub' in args:
    #     options["subtitle_language"] = args[args.index('--sub') + 1]
    # # content rating
    # if '-cr' in args:
    #     options["content_rating"] = args[args.index('-cr') + 1]
    # elif '--contentrating' in args:
    #     options["content_rating"] = args[args.index('--contentrating') + 1]
    # if '-sim' in args:
    #     similar = True
    # elif '--similar' in args:
    #     similar = True
    # if '-sum' in args:
    #     summary = True
    # elif '--summary' in args:
    #     summary = True
    # print(f'parameters set: {options}')

    # User entered simply "plex search"
    # if not args[0]:
    #     result = ['Please specify a search parameter. ' \
    #            'See `plex search help` for more information.']
    # # Handle specific search cases
    # if args[0] in {'library', 'libraries', 'lib', 'libs'}:
    #     result = get_library_list()
    # # Determine library
    # # We require this of the user to prevent search results taking too long
    # elif {args[0], options["library"]}.intersection({
    #     'movie', 'movies', 'film', 'films'}):
    #     options["library"] = 'Movies'
    # elif {args[0], options["library"]}.intersection({
    #     'music', 'songs'}):
    #     options["library"] = 'Music'
    # elif {args[0], options["library"]}.intersection({
    #     'tv', 'television', 'tv shows', 'shows'}):
    #     options["library"] = 'TV Shows'
    # else:
    #     if not options["library"]:
    #         options["library"] = 'Movies'
    # print(f'library determined: {options["library"]}')
    #
    # if args[0] in {'random', 'rand'}:
    #     result = get_random(options)
    # elif args[0] in {'collection', 'collections'}:
    #     result = get_collections_list(options)
    # # elif args[0] in {'unwatched'}:
    # #     result = get_unwatched(options)
    # elif args[0] in {'inprogress'}:
    #     result = get_in_progress(options)
    # elif args[0] in {'recent', 'new'}:
    #     result = get_recently_added(options)

    # print('sim check')

    # elif '-sim' in args :
    #     similar = True
    # print(f'special searches passed')

    if options["id"]:
        result = search_hltb_by_id(options)

    # Generic search
    if not result:
        result, similar = search_hltb(options)
    return [result, similar]


@debug
def search_hltb(options: dict) -> tuple:
    """

    :param options:
    :return:
    """
    best_element = None
    results_list = HowLongToBeat().search(options["title"])
    multiple = False
    if results_list is not None and len(results_list) > 1:
        multiple = True
        for each in results_list:
            best_element = [f'{each.game_name} {each.similarity * 100:.2f}% -- {each.game_id}' for each in results_list]
        # Saving in case I decide to do 'pick best automatically'
        # best_element = max(results_list, key=lambda element: element.similarity)
    else:
        best_element = results_list
    return best_element, multiple


@debug
def search_hltb_by_id(options: dict) -> list:
    """

    :param options:
    :return:
    """
    result = HowLongToBeat().search_from_id(options['id'])
    return [result]


def get_search_help() -> str:
    """
    Return help file for usage
    :return:
    """
    return """
    ```
    Search How Long To Beat dot com.
    
    If more than one matching title is found a list will be provided with:
    {game name} {similarity percentage} -- {game id}
    If this happens, use the -id option to get the game you want.
    

    hltb search <title>
    hltb search <option> <title>

    Options:
      -h --help            Show this help prompt
      -id                  Search by id
    ```
    """

# TODO update to match when finished
def get_help():
    pass

