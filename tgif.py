#!/usr/bin/python3


import random
from os import listdir
from os.path import isdir
import aiohttp
import aiofiles
from pathlib import Path

from discord import Embed

from tutil import increment_usage, fetch_file
from constants import DEFAULT_DIR, VERBOSE


def get_react(message):
    """
    Get a random gif file from ./emotes or the servers folder
    :param message: <Discord.message object>
    :return: <String> Describing file location
    """
    increment_usage(message.guild, 'gif')

    nsfw = True if 'nsfw' in message.content.lower() else False
    guild = message.guild.id
    reacts = ['{}/emotes/{}'.format(DEFAULT_DIR, each) for each in listdir('./emotes')]

    if isdir('{}/emotes/{}'.format(DEFAULT_DIR, guild)):
        reacts.extend(
            ['{}/emotes/{}/{}'.format(DEFAULT_DIR, guild, each) for each in listdir('./emotes/{}'.format(guild))])

    if nsfw and isdir('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, guild)):
        reacts.extend(['{}/emotes/{}/nsfw/{}'.format(DEFAULT_DIR, guild, each) for each in
                       listdir('./emotes/{}/nsfw'.format(guild))])

    return random.choice(reacts)


async def fetch_react(message):
    """
    Save a gif a user added with !gif add
    :param message: <Discord.message object>
    :return: <String> Notify of gif being added or not
    """
    increment_usage(message.guild, 'gif')
    url = str(message.attachments[0].url)
    extension = str(url.split('.')[-1].lower())

    if extension != 'gif':
        return 'File must be a gif'

    file_name = str(url.split('/')[-1])
    nsfw = True if 'nsfw' in message.content.lower() else False

    if nsfw:
        Path('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, message.guild.id)).mkdir(parents=True, exist_ok=True)
        file_path = '{}/emotes/{}/nsfw/{}'.format(DEFAULT_DIR, message.guild.id, file_name)
    else:
        Path('{}/emotes/{}'.format(DEFAULT_DIR, message.guild.id)).mkdir(parents=True, exist_ok=True)
        file_path = '{}/emotes/{}/{}'.format(DEFAULT_DIR, message.guild.id, file_name)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(file_path, mode='wb')
                await f.write(await resp.read())
                await f.close()
                if VERBOSE >= 2:
                    print("[+] Saved: {}".format(file_path))
                return 'Added a new gif to !gif'


def get_help(author):
	"""
	Get the help file in ./docs/help
	:param message: <Discord.message.author object>
	:return: <String> The local help file
	"""
	text = fetch_file('help', 'gif')
	banner = Embed(title='General Help', description=text)
	return banner
