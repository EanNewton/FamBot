from random import choice

import discord
from discord import Embed
from discord import File as DiscordFile

import thltb
import tword
import tquote
import tsched
import tlog
import tstat
# import tcustom
import tgif
import tplex
from tutil import is_admin, config_helper, fetch_file, increment_usage, debug, is_admin_test
# from speller import Speller
from constants import EIGHTBALL, DEFAULT_DIR, help_general, VERBOSE


# Break out functions to prevent dispatch() from
# becoming overly lengthy
async def get_quote(result: dict) -> dict:
    """
    Pass off to tquote.py
    :param result:
    :return:
    """
    banner = await tquote.helper(result["message"])
    if type(banner) is str:
        result["rawText"] = banner
    elif type(banner) is list:
        result["rawText"] = banner[0]
        result["file"] = banner[1]
    else:
        result["embed"] = banner
    return result


async def get_plex(result: dict) -> dict:
    """
    Pass off to tplex.py
    :param result:
    :return:
    """
    # TODO add rich embeds
    banner = await tplex.helper(result["message"])
    result["rawText"] = banner
    return result


async def get_hltb(result: dict) -> dict:
    """
    Pass off to thltb.py
    How Long to Beat dot com search results.
    :param result:
    :return:
    """
    # TODO build this out
    # TODO add rich embeds
    banner = await thltb.helper(result["message"])
    result["rawText"] = banner
    return result


async def get_wolfram(result: dict) -> dict:
    """
    Pass off to tword.py
    :param result:
    :return:
    """
    banner = await tword.wolfram(result["message"])
    if type(banner) is list:
        result["rawText"] = banner[0]
        result["file"] = banner[1]
    else:
        result["embed"] = banner
    return result


async def get_gif(result: dict) -> dict:
    """
    Pass off to tgif.py
    :param result:
    :return:
    """
    args = result["message"].content.split()
    if len(args) > 1 and args[1] == 'add':
        await tgif.fetch_react(result["message"])
    else:
        result["file"] = tgif.get_react(result["message"])
    return result


async def get_help(result: dict) -> dict:
    """
    Return help text.
    :param result:
    :return:
    """
    increment_usage(result["message"].guild, 'help')
    help_ = fetch_file('help', 'general')
    if not await is_admin(result["message"].author, result["message"]):
        help_ = help_.split('For Admins:')[0]

    banner = Embed(title='General Help', description=help_)
    banner.add_field(name='Help support this bot!', value='All donations go to development and server costs.',
                     inline=False)
    banner.add_field(name='PayPal', value=help_general['paypal'])
    # TODO patreon + invite?
    # banner.add_field(name='Patreon', value=help_general['patreon'])
    banner.add_field(name='More Information',
                     value='This bot is open source, find it at: {}'.format(help_general['github']))
    banner.add_field(name='Invite the bot to your server.', value=help_general['invite'], inline=False)

    result["embed"] = banner
    return result


async def dispatch(message: discord.Message) -> (None, dict):
    """
    Process raw discord.Message object and send it to dedicated function.
    :param message:
    :return:
    """
    # print(message)
    # print(message.content)
    # Preprocessing
    # Prevent recursive loops or triggering from other bots.
    if message.author.bot:
        return None
    # TODO implement this into config
    # Confirm we are in an approved channel
    # if len(config['discord']['AllowedChannels']) > 0 and str(channel.id) not in config['discord'][
    #     'AllowedChannels'].split(','):
    #     return
    # Register a new message in the database
    increment_usage(message.guild, 'raw_messages')
    await tlog.log_message(message)
    # Setup for checking commands
    args = message.content.split()
    result = {"message": message, "rawText": None, "embed": None, "file": None}
    # TODO redo logging
    if VERBOSE >= 2:
        print('[-] {} by {} in {} - {}'.format(args[0][1:], message.author.name, message.channel.name, message.guild.name))

    # Guild level custom commands
    # custom = tcustom.get_command(message)
    # custom = None
    custom = False
    if custom:
        if VERBOSE >= 2:
            print('[-] {} by {} in {} - {}'.format(
                'arg: {}'.format(args[0]), message.author.name, message.channel.name, message.guild.name))
        result["rawText"] = custom[0]
        result["embed"] = custom[1]
        return result

    # Correct minor typos
    # TODO rewrite library defs before using
#    print('correcting typos')
    # spell = Speller('cmd')
    # operator = spell(args[0][1:])
 #   print(args)
    operator = args[0][1:]
    # TODO move this config.ini + constants file
    if args[0][0] != '!':
        return None
    if VERBOSE >= 2:
        print('[-] {} by {} in {} - {}'.format(operator, message.author.name, message.channel.name, message.guild.name))

    # Quotes
    if operator in {'quote', 'lore', 'q', 'l'}:
        # print('getting quote')
        result = await get_quote(result)

    # TODO update link
    if operator in {'invite'}:
        result["rawText"] = "https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=7433793&scope=bot"
        return result

    # Plex Media Server
    if operator in {'plex', 'movie', 'movies'}:
        # print('calling plex')
        result = await get_plex(result)

    # How Long to Beat
    if operator in {'hltb'}:
        # print('calling hltb')
        result = await get_hltb(result)

    # Wolfram Alpha
    elif operator in {'w', 'wolf', 'wolfram'}:
        result = await get_wolfram(result)

    # Word of the Day
    elif operator in {'word', 'wotd'}:
        result["embed"] = await tword.get_todays_word(message)

    # Wiktionary
    elif operator in {'dict', 'dictionary', 'wiki', 'wiktionary'}:
        result["embed"] = tword.wiki(message)

    # Config
    elif operator == 'config':
        result["file"] = await config_helper(message)
        if result["file"] and type(result["file"]) is not DiscordFile:
            result["file"] = DiscordFile(result["file"])
        await message.author.send(file=result["file"])
        return None

    # Log
    elif operator == 'log' and await is_admin_test(message.author, message):
        banner = tlog.get_log(message)
        result["file"] = banner[1]
        if result["file"] and type(result["file"]) is not DiscordFile:
            result["file"] = DiscordFile(result["file"])
        await message.author.send(content=banner[0], file=result["file"])
        return None

    # Schedule
    elif operator in {'schedule', 'sched', 's'}:
        result["embed"] = tsched.helper(message)
    elif operator in {'next'}:
        result["embed"] = tsched.helper(message, 'next')

    # Yandex
    elif operator in {'yandex', 'image', 'tineye', 'reverse'}:
        result["rawText"] = tword.yandex(message)

    # Doip
    elif operator == 'doip' and int(message.guild.id) == 453859595262361611:
        increment_usage(message.guild, 'doip')
        result["rawText"] = tquote.get_quote(message, tquote.Quotes, "LaDoIphin", True)
        result["file"] = '{}/docs/doip.jpg'.format(DEFAULT_DIR)

    # GIF
    elif operator in {'gif', 'react', 'meme'}:
        return await get_gif(result)

    # Stats
    elif operator == 'stats':
        result["file"], result["embed"] = tstat.helper(message)

    # Magic Eightball
    elif operator in {'8ball', '88ball', 'ball', '8', 'eightball', 'eight'}:
        increment_usage(message.guild, 'eight')
        result["rawText"] = choice(EIGHTBALL)

    # General Help
    elif operator == 'help':
        result = await get_help(result)

    if result["file"] and type(result["file"]) is not DiscordFile:
        result["file"] = DiscordFile(result["file"])

    return result
