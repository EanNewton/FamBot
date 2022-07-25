from random import choice

import discord
from discord import Embed
from discord import File as DiscordFile

import tword
import tquote
import tsched
import tlog
import tstat
import tcustom
import tgif
from tutil import is_admin, config_helper, fetch_file, increment_usage, debug, is_admin_test
from speller import Speller
from constants import EIGHTBALL, DEFAULT_DIR, help_general, VERBOSE

# Break out functions to prevent dispatch() from
# becoming overly lengthy
def get_quote(result: dict) -> dict:
    """
    Pass off to tquote.py
    :param result:
    :return:
    """
    banner = tquote.helper(result["message"])
    if type(banner) is str:
        result["rawText"] = banner
    elif type(banner) is list:
        result["rawText"] = banner[0]
        result["file"] = banner[1]
    else:
        result["embed"] = banner
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
        await tgif.get_react(result["message"])
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

@debug
async def dispatch(message: discord.Message) -> (None, dict):
    """
    Process raw discord.Message object and send it to dedicated function.
    :param message:
    :return:
    """
    # Preprocessing
    # Prevent recursive loops or triggering from other bots.
    if message.author.bot:
        return None
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
    custom = tcustom.get_command(message)
    if custom:
        if VERBOSE >= 2:
            print('[-] {} by {} in {} - {}'.format(
                'arg: {}'.format(args[0]), message.author.name, message.channel.name, message.guild.name))
        result["rawText"] = custom[0]
        result["embed"] = custom[1]
        return result

    # Correct minor typos
    spell = Speller('cmd')
    operator = spell(args[0][1:])
    if args[0][0] != '$':
        return None
    if VERBOSE >= 2:
        print('[-] {} by {} in {} - {}'.format(operator, message.author.name, message.channel.name, message.guild.name))

    # Quotes
    if operator in {'quote', 'lore', 'q', 'l'}:
        result = get_quote(result)

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