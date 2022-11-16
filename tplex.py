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
regex_is_year = "\d{4}"

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
    ops = {'list', 'search', 'help', 'invite', 'year'}

    operator = 'get'
    if len(args) > 1 and args[1] in ops:
        operator = args[1]
    if op_override:
        operator = op_override

    return {
        'list': lambda: list_parse(args),
        'year': lambda: list_parse(args)
        'search': lambda: search_parse(args),
        'help': lambda: help(),
    }.get(operator, lambda: None)()


@debug
def list_parse(args):
    year = None
    if 'tv' in args:
        pass
    #     return list_tv(args[2:])
    elif 'movie' in args:
        # List all movies from certain year
        year = re.findall(regex_is_year, args[-1])
        if year:
            return list_movies_year(args[-1])
        # List all movies matching title
        else:
            return list_movies(args[2:])
    elif 'music' in args:
        pass
    #     return list_music(args[2:])
    else:
        return 'Please specify whether to search `movie`, `tv`, or `music`.'

@debug
def list_movies(args: list) -> list:
    movies = plex.library.section('Movies')
    msg = ''
    if 'unwatched' in args:
        for video in movies.search(unwatched=True):
            msg = f'{msg}{video.title}\n'
    elif 'random' in args:
        choice = random.choice(movies.search())
        msg = f'{choice.title} ({choice.year})'
    else:
        for video in movies.search():
            msg = f'{msg}{video.title}\n'
    return wrap(msg, 1999)


@debug
def list_movies_year(year: str) -> list:
    """
    List all movies released in a specified year.
    :param year:
    :return:
    """
    msg = 'No movie found'
    movies = plex.library.section('Movies')
    result = movies.all(year=year)
    if len(result) > 0:
        for video in result:
            msg = f'**{year}**\r{DIVIDER}\r`{video.title}`\r'
    return wrap(msg, 1999)


@debug
def search_parse(args):
    if 'tv' in args:
        return search_tv(args[2:])
    elif 'movie' in args:
        return search_movies(args[3:])
    elif args[1].lower() == 'music':
        pass
    #  return search_music(args[2:])
    else:
        return 'Please specify whether to search `movie`, `tv`, or `music`.'


@debug
def search_movies(args: list) -> list:
    # Define blank message
    msg = 'No movie found'
    year = None
    name = ' '.join(args).strip()
    # Check if specific year was requested to avoid remakes
    year = re.findall(regex_is_year, args[-1])
    # Get the name of the movie from the message
    # Define the movie library
    movies = plex.library.section('Movies')
    if year:
        name = ' '.join(args[:-1]).strip()
        result = movies.search(name, year=year)
    else:
        result = movies.search(name)
    if len(result) > 0:
        # Loop through the search results and add them to the message
        for video in result:
            msg = f'{msg}`{video.title} - {video.year}`\r'
    return wrap(msg, 1999)


def search_tv(args):
    # Define blank message
    msg = ''
    # Get the name of the video from the message
    name = ' '.join(args[1])
    # Define the tv library
    tv = plex.library.section('TV Shows')
    if len(tv.search(name)) > 0:
        # Loop through the search results and add them to the message
        for video in tv.search(name):
            msg = msg + "```\r" + video.title
            for season in video.seasons():
                msg = msg + "\rSeason " + str(season.index) + "\r"
                for episode in season.episodes():
                    msg = msg + str(episode.index) + " "
        msg = msg + '```'
    else:
        msg = 'No TV show found'
    # Send message with search results
    return wrap(msg, 1999)


# TODO update to match when finished
def help():
    # Print out commands available
    return '**!search {movie}** Search for a movie by name\r' \
           '**!play {movie}** Play a movie using the exact name from the search command\r' \
           '**!pause** Pause the movie\r' \
           '**!resume** Resume the paused movie\r' \
           '**!stop** Stop the movie\r' \
           '**!tvsearch {tv_name}** Search for a tv show by name\r' \
           '**!tvplay {tv_name} -s={season_number} -e={episode_number}** Play an episode of TV'



    # TODO unused artifact code
    # # On Discord message
    # @client.event
    # async def on_message(message):
    #     global videoPlaying
    #     global ffmpegID
    #     global plexClient
    #     channel = message.channel
    #
    #     if len(config['discord']['AllowedChannels']) > 0 and str(channel.id) not in config['discord'][
    #         'AllowedChannels'].split(','):
    #         return
    #
    #
    # # Start discord client
    # client.run(config['discord']['Key'])


    # TODO the following need a rewrite, vangel.io does not exist
    # TODO plex remote control is dead. Need to find another method. client list is always empty
    # def plex_play():
    #     # Message is command to play movie
    #     elif message.content.startswith('!play'):
    #         # If a movie is already playing discard message and notify
    #         if videoPlaying == True:
    #             await channel.send('Stream is already playing')
    #         else:
    #             msg = ''
    #             name = message.content[len('!play'):].strip()
    #             # Get movie information from plex
    #             try:
    #                 movie = plex.library.section('Movies').get(name)
    #             except:
    #                 search = plex.library.section('Movies').search(name)
    #                 if len(search) == 1:
    #                     movie = search[0]
    #
    #             # Set the game the bot is playing to the movie name
    #             game = discord.Game(movie.title)
    #             await client.change_presence(status=discord.Status.idle, activity=game)
    #
    #             # Set the global movie playing variable so there aren't duplicate videos trying to stream
    #             videoPlaying = True
    #             streamID = secrets.token_urlsafe(8)
    #             # Send message to confirm action
    #             await channel.send('Streaming ' + movie.title + '\rhttps://stream.vangel.io/?=' + streamID)
    #             p = Process(target=start_stream, args=(message, movie.locations[0], streamID,))
    #             p.start()
    #
    #
    # def plex_stop():
    #     # Video stop command
    #     elif message.content.startswith('!stop'):
    #         try:
    #             ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
    #             # Kill the ffmpeg process
    #             subprocess.run(["kill", ffmpegID])
    #         except:
    #             print("No video playing")
    #         # Clear the game playing information
    #         await client.change_presence(status=discord.Status.idle, activity=None)
    #         # Set the video playing variable to false to allow a new video to be streamed
    #         videoPlaying = False
    #         # Send message to confirm action
    #         await channel.send('Stopping Stream')
    #
    #
    # def plex_resume():
    #     elif message.content.startswith('!resume'):
    #         ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
    #         # Resume the ffmpeg process
    #         subprocess.run(["kill", "-s", "SIGCONT", ffmpegID])
    #         # Send message to confirm action
    #         await channel.send('Resuming Stream')
    #
    # def plex_pause():
    #     # Pause command
    #     elif message.content.startswith('!pause'):
    #         ffmpegID = subprocess.check_output(["pgrep", "ffmpeg"]).strip().decode('ascii')
    #         # Suspend the ffmpeg process
    #         subprocess.run(["kill", "-s", "SIGSTOP", ffmpegID])
    #         # Send message to confirm action
    #         await channel.send('Pausing Stream')


    # def plex_tvplay():
    #     elif message.content.startswith('!tvplay'):
    #         # Define blank message
    #         msg = ''
    #         # Get the name of tv from the message
    #         season = message.content.find("-s=")
    #         episode = message.content.find("-e=")
    #         name = message.content[len('!tvplay'):season].strip()
    #         seasonNumber = message.content[season + 3:episode].strip()
    #         episodeNumber = message.content[episode + 3:].strip()
    #         # Define the tv library
    #         tv = plex.library.section('TV Shows')
    #         searchResult = tv.search(name)
    #         print(searchResult)
    #         if len(searchResult) > 1:
    #             await channel.send('Refine search result to one show')
    #         elif len(searchResult) > 0:
    #             # Loop through the search results and add them to the message
    #             for video in searchResult:
    #                 for season in video.seasons():
    #                     for episode in season.episodes():
    #                         if str(season.index) == str(seasonNumber) and str(episode.index) == str(episodeNumber):
    #                             game = discord.Game(episode.title)
    #                             await client.change_presence(status=discord.Status.idle, activity=game)
    #                             # Set the global video playing variable so there aren't duplicate videos trying to stream
    #                             videoPlaying = True
    #                             streamID = secrets.token_urlsafe(8)
    #                             ## Send message to confirm action
    #                             await channel.send(
    #                                 'Streaming ' + episode.title + '\rhttps://stream.vangel.io/?=' + streamID)
    #                             p = Process(target=start_stream, args=(message, episode.locations[0], streamID,))
    #                             p.start()
    #         else:
    #             await channel.send('No episode or TV show matching that name found')


    # TODO unused?
    # def start_stream(message, path, id):
    #     global client
    #     # Update path so its accurate on the stream server
    #     for x in config['plex']['RemappedFolders'].split(","):
    #         oldPath, newPath = x.split(":")
    #         path = path.replace(oldPath, newPath)
    #     url = config['stream']['Destination'] + id
    #     # Start streaming the video using ffmpeg
    #     subprocess.call([config['stream']['FFMPEGLocation'], "-re", "-i", path, "-c:v", "libx264", "-filter:v",
    #                      "scale=1280:trunc(ow/a/2)*2", "-preset", "fast", "-minrate", "500k", "-maxrate", "3500k",
    #                      "-bufsize", "12M", "-c:a", "libfdk_aac", "-b:a", "160k", "-f", "flv", url])



    # def youtube_play():
    # elif message.content.startswith('!youtubeplay'):
    #     name = message.content[len('!youtubeplay'):].strip()
    #     if validators.url(name) == True:
    #         parsed_uri = urlsplit(name)
    #         if parsed_uri.hostname == "www.youtube.com" or parsed_uri.hostname == "youtube.com" or parsed_uri.hostname == "youtu.be"  or parsed_uri.hostname == "www.youtu.be":
    #             await client.change_presence(game=discord.Game(name='Youtube'))
    #             # Set the global movie playing variable so there aren't duplicate movies trying to stream
    #             videoPlaying = True
    #             ## Send message to confirm action
    #             await channel.send('Streaming Youtube')

    #             devnull = open('/dev/null', 'w')
    #             # Start streaming the movie using ffmpeg
    #             # Path to movie is pulled from the plex api because the paths are the same on both machines
    #             command = "youtube-dl -f 'best[ext=mp4]' -o - \""+name+"\" | ffmpeg -re -i pipe:0 -c:v copy -preset fast -c:a copy -f flv "+ config['stream']['Destination']
    #             print(command)
    #             subprocess.call(command.split(), shell=False)
    #     else:
    #         await channel.send('Invalid url')

