#!/usr/bin/python3
# TODO standardize help
# TODO create a git commit for server join count
# TODO server invite link
# TODO update help files
# TODO redo the logging to actually be useful
# TODO fix mention suppression on quotes

import logging

import pendulum
import discord

import switchboard
import tquote
import tcustom
from tutil import is_admin, config_create, fetch_file, is_admin_test
from tutil import setup as util_setup
from constants import TOKEN, POC_TOKEN, VERSION, DIVIDER, VERBOSE, DEFAULT_DIR

bot = discord.Client()


@bot.event
async def on_ready() -> None:
    print(
        f'{bot.user} has connected to Discord!\n'
        f'Revision date: {VERSION}\n'
    )
    if VERBOSE >= 0:
        count = 0
        for each in bot.guilds:
            print(
                f'{each.name}(id: {each.id})\n'
                f'Member count: {each.member_count}'
            )
            count += each.member_count
        print(DIVIDER)
        print('Total guilds: {}'.format(len(bot.guilds)))
        print('Total members: {}'.format(count))


@bot.event
async def on_guild_join(guild: discord.guild) -> None:
    """
    Create a blank new config in the database and send a DM to the guild owner.
    :param guild:
    :return:
    """
    if VERBOSE >= 1:
        print('[+] Joined a new guild: {}'.format(guild.name))
    config_file = config_create(guild)
    banner = 'Hello {}! \n{}'.format(guild.owner.mention, fetch_file('help', 'welcome'))
    await guild.owner.send(file=discord.File('{}/docs/header.png'.format(DEFAULT_DIR)))
    await guild.owner.send(banner, file=discord.File(config_file))
    tquote.setup()
    util_setup()


@bot.event
async def on_message(message: discord.Message) -> None:
    """
    Dispatch the raw message object to switchboard.py
    Switchboard filters input then redirects to dedicated functions
    Send discord.message object to Discord API for posting, return None
    :param message:
    :return:
    """
    banner = await switchboard.dispatch(message)

    if banner:
        if banner["rawText"] and banner["file"]:
            await message.channel.send(banner["rawText"], file=banner["file"])

        elif banner["embed"] and banner["file"]:
            await message.channel.send(embed=banner["embed"], file=banner["file"])

        elif banner["embed"]:
            if type(banner["embed"]) is list:
                await message.channel.send(embed=banner["embed"][0])
                await message.channel.send(embed=banner["embed"][1])
            else:
                await message.channel.send(embed=banner["embed"])

        elif banner["file"]:
            await message.channel.send(file=banner["file"])

        elif banner["rawText"]:
            await message.channel.send(banner["rawText"])
#        else:
 #           await message.channel.send("No results.")


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
    """
    Called whenever a reaction is added to a message.
    Using on_raw_reaction_add() instead of on_reaction_add() because
    on_raw is called regardless of the state of the internal message cache.
    Python and Discord are picky about the emoji string comparison, if
    you encounter issues, keep trying different things.
    :param payload:
    :return:
    """
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    print(payload)
    print(payload.emoji)

    # Add a quote
    # emoji is :speech_left:
    if str(payload.emoji) == '🗨️' and not message.author.bot:
        print('caught speech')
        if not tquote.check_if_exists(message.guild.id, message.id):
            print('does not exist yet')
            banner = tquote.insert_quote(message, None, payload.member.name)
            if VERBOSE >= 2:
                print('[+] Added quote {}.'.format(banner))
            await message.channel.send(embed=banner)

    # Remove a quote
    # emoji is :x:
    if str(payload.emoji) == '❌' and await is_admin_test(payload.member, message):
        try:
            banner = tquote.delete_quote(message.guild.id, message.id)
            if VERBOSE >= 2:
                print('[+] Deleted quote: {}'.format(banner))
            await message.channel.send(banner)
        except Exception as e:
            if VERBOSE >= 1:
                print('[!] Exception in Remove quote: {}'.format(e))
            pass
        if VERBOSE >= 2:
            print('[+] Deleting command.')
        await message.channel.send(await tcustom.delete_command(message))

    # Add a custom guild command
    # emoji is :gear:
    if str(payload.emoji) == '⚙️' and await is_admin_test(payload.member, message):
        if VERBOSE >= 2:
            print('[+] Added command.')
        await message.channel.send(embed=tcustom.insert_command(message))


# TODO redo logging with loguru
@bot.event
async def on_error(event, *args, **kwargs):
    # For errors with the bot itself
    with open('./log/err.log', 'a') as f:
        if event == 'on_message':
            timestamp = pendulum.now(tz='America/Phoenix').to_datetime_string()
            location = '[!] Error in: {}; {}'.format(args[0].channel.name, args[0].guild.name)
            content = '[!] Error content: {}'.format(args[0].content)
            author = '[!] Error author: {}'.format(args[0].author)

            f.write('{}\nUnhandled message:{}\n{}\n{}\n{}\n\n'.format(
                timestamp,
                args[0],
                location,
                author,
                content,
            ))
        else:
            return

bot.run(TOKEN)
