import discord
from howlongtobeatpy import HowLongToBeat

from tutil import flatten_sublist
from tutil import debug
from constants import DIVIDER, VERBOSE

regex_is_year = r"\d{4}"


async def helper(message: discord.Message, op_override=None):
    """
    Main entry point from main.py
    :param op_override: Activate a specific operator
    :param message: <Discord.message object>
    :return: <lambda function> Internal function dispatch
    """

    args = message.content.split()
    ops = {'search', 'help'}
    operator = 'search'
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


def rendered(message: list) -> str:
    """
    Convert raw results to something Discord safe.
    :param message:
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
    args = [arg.split('=') for arg in args]
    args = flatten_sublist(args)
    # args = args.strip()
    # Add if statement to this to avoid -D becoming equivalent to -d, etc
    args = [arg.lower().strip() if not arg.startswith('-') else arg for arg in args]
    # TODO add Speller library
    args = args[1:]
    if VERBOSE >= 2:
        print(f'args are: {args}')

    # Setup blanks
    options = {
        "library": None,
        "limit": None,
        "title": None,
        "id": None
    }
    result = None
    similar = False
    summary = False
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

    # Handle special options
    # help
    if {'-h', '--help'}.intersection(args):
        return get_search_help()
    # all
    if {'-id'}.intersection(args):
        options["id"] = int(args[args.index('-id') + 1])

    if options["id"]:
        result = search_hltb_by_id(options)

    # Generic search
    if not result:
        result, similar = search_hltb(options)
    return [result, similar]


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


def search_hltb_by_id(options: dict) -> list:
    """

    :param options:
    :return:
    """
    return [HowLongToBeat().search_from_id(options['id'])]


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

