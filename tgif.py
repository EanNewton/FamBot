#!/usr/bin/python3
import os.path
import random
from os import listdir
from os.path import isdir, exists
from pathlib import Path
from platform import system

import aiofiles
import aiohttp
import discord

from constants import DEFAULT_DIR, VERBOSE
from tutil import increment_usage
# from tutil import debug

running_os = system()


def get_react(message: discord.Message) -> str:
    """
    Get a random gif file from ./emotes or the servers folder
    :param message: <Discord.message object>
    :return: <String> Describing file location
    """
    increment_usage(message.guild, 'gif')

    # TODO collapse into single statement / DRY
    if exists('./emotes') and running_os == 'Linux':
        # Generate a list of possible gif files to choose from
        reacts = [os.path.abspath("emotes/"+file) for file in listdir('./emotes')]
        guild = message.guild.id
        # Include guild-specific results
        if isdir('{}/emotes/{}'.format(DEFAULT_DIR, guild)):
            reacts.extend(
                [os.path.abspath('emotes/{}/{}'.format(guild, each)) for each in
                 listdir('./emotes/{}'.format(guild))])
        # Include guild-specific nsfw results
        if 'nsfw' in message.content.lower() and isdir('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, guild)):
            reacts.extend([os.path.abspath('emotes/{}/nsfw/{}'.format(guild, each)) for each in
                           listdir('./emotes/{}/nsfw'.format(guild))])
        return random.choice(reacts)

    if exists('./emotes') and running_os == 'Windows':
        # Generate a list of possible gif files to choose from
        reacts = [os.path.abspath("emotes\\"+file) for file in listdir('./emotes')]
        guild = message.guild.id
        # Include guild-specific results
        if isdir('{}/emotes/{}'.format(DEFAULT_DIR, guild)):
            reacts.extend(
                [os.path.abspath('emotes\\{}\\{}'.format(guild, each)) for each in
                 listdir('./emotes/{}'.format(guild))])
        # Include guild-specific nsfw results
        if 'nsfw' in message.content.lower() and isdir('{}/emotes/{}/nsfw'.format(DEFAULT_DIR, guild)):
            reacts.extend([os.path.abspath('emotes\\{}\\nsfw\\{}'.format(guild, each)) for each in
                           listdir('./emotes/{}/nsfw'.format(guild))])
        return random.choice(reacts)

    return "Emotes directory does not exist."


# TODO untested
async def fetch_react(message: discord.Message) -> str:
    """
    Save a gif a user added with !gif add
    :param message: <Discord.message object>
    :return: <String> Notify of gif being added or not
    """
    increment_usage(message.guild, 'gif')
    url = str(message.attachments[0].url)
    file_name = str(url.split('/')[-1])
    extension = str(url.split('.')[-1].lower())

    if extension != 'gif':
        return 'File must be a gif'

    if 'nsfw' in message.content.lower():
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


# TODO this is unused
# def get_help(author):
#     """
#     Get the help file in ./docs/help
#     :param message: <Discord.message.author object>
#     :return: <String> The local help file
#     """
#     text = fetch_file('help', 'gif')
#     banner = Embed(title='General Help', description=text)
#     return banner
