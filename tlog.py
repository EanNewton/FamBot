#!/usr/bin/python3

import aiohttp
import aiofiles
from pathlib import Path

import pendulum
import pandas as pd
from sqlalchemy import and_, MetaData, Table, Column, Integer, String, select

from tutil import fetch_file, is_admin, config_fetch_embed, debug
from constants import DEFAULT_DIR, ENGINE, VERBOSE

extSet = {}
# TODO redo the entirety of logging

def setup():
    global meta, Corpus
    meta = MetaData()
    Corpus = Table(
        'corpus', meta,
        Column('id', Integer, primary_key=True),
        Column('content', String),
        Column('user_name', String),
        Column('user_id', String),
        Column('time', String),
        Column('channel', String),
        Column('embeds', String),
        Column('attachments', String),
        Column('mentions', String),
        Column('channel_mentions', String),
        Column('role_mentions', String),
        Column('msg_id', String),
        Column('reactions', String),
        Column('guild', String),
        Column('guild_name', String),
    )
    meta.create_all(ENGINE)
    for file_ in {'audio', 'docs', 'images', 'video'}:
        f = fetch_file('ext', file_).strip('\n')
        extSet[file_] = f.split()

    if VERBOSE >= 0:
        print('[+] End Logger Setup')


async def log_message(message):
    """
	Grab new config file if present and add each raw message to the database. 
	:param message: <Discord.message object>
	:return: <None>
	"""
    timestamp = pendulum.now(tz='Asia/Tokyo').to_datetime_string()
    corpus_insert(message, timestamp)

    if message.attachments:
        await fetch_embed(message, timestamp)
        if await is_admin(message.author, message) and message.attachments[0].file_name == '{}.json'.format(message.guild.id):
            await config_fetch_embed(message)


def corpus_insert(message, time_stamp):
    """
	For bulk logging of all messages sent in all servers. Used for stats and admin logs.
	:param message: <Discord.message object>
	:param timeStamp> <String> The current server time
	:return: <None>
	"""
    msg_mentions = [''.join(str(each)) for each in message.mentions]
    msg_embeds = [''.join(str(each.to_dict())) for each in message.embeds]
    msg_attachments = [''.join(str(each.file_name)) for each in message.attachments]
    msg_channel_mentions = [''.join(str(each)) for each in message.channel_mentions]
    msg_role_mentions = [''.join(str(each)) for each in message.role_mentions]

    with ENGINE.connect() as conn:
        ins = Corpus.insert().values(
            content=str(message.content),
            user_name=str(message.author),
            user_id=str(message.author.id),
            time=str(time_stamp),
            channel=str(message.channel),
            embeds=str(msg_embeds),
            attachments=str(msg_attachments),
            mentions=str(msg_mentions),
            channel_mentions=str(msg_channel_mentions),
            role_mentions=str(msg_role_mentions),
            msg_id=str(message.id),
            reactions="none",
            guild=str(message.guild.id),
            guild_name=str(message.guild.name),
        )
        conn.execute(ins)


async def fetcher(filetype, url, time, message):
    """
	Internal function to download any message attachments from Discord servers
	:param filetype: <String> The file extension
	:param url: <String> The file location URL
	:param time: <String> Current server time
	:param message: <Discord.message object>
	:return: <None>
	"""
    file_name = '{}_{}_{}'.format(message.author.name, time, url.split('/')[-1])
    Path('{}/log/{}/{}/{}'.format(
        DEFAULT_DIR, filetype, message.guild.name, message.channel.name)).mkdir(
        parents=True, exist_ok=True)
    file_path = '{}/log/{}/{}/{}/{}'.format(
        DEFAULT_DIR, filetype, message.guild.name, message.channel.name, file_name)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(file_path, mode='wb')
                await f.write(await resp.read())
                await f.close()
                if VERBOSE >= 1:
                    print("[+] Saved: {}".format(file_path))


async def fetch_embed(message, time):
    """
	Call fetcher() for each message.attachment
	:param message: <Discord.message object>
	:param time: <String> Current server time
	:return: <None>
	"""
    url = str(message.attachments[0].url)
    ext = str(url.split('.')[-1].lower())
    [await fetcher(each, url, time, message) for each in extSet if ext in extSet[each]]

@debug
def get_log(message):
    """
	Get an excel file log of a guild
	:param message: <Discord.message object>
	:return: <List> Describing output and file location
	"""

    args = message.content.split()
    if VERBOSE >= 2:
        print(args)

    if len(args) > 2:
        # Get log of a specific user
        if args[1] in {"user"}:
            try:
                for each in message.mentions:
                    user = each.id
            except:
                pass

            select_st = select([Corpus]).where(and_(
                Corpus.c.guild == message.guild.id,
                Corpus.c.user_id == user))
            df = [None]
            with ENGINE.connect() as conn:
                result = conn.execute(select_st).fetchall()
                keys = conn.execute(select_st).keys()

                entries = [each.values() for each in result]
                for each in entries:
                    each[0] = 'id_{}'.format(each[0])
                    each[3] = 'uid_{}'.format(each[3])
                    each[11] = 'mid_{}'.format(each[11])
                    each[13] = 'gid_{}'.format(each[13])

                df[0] = pd.DataFrame(entries, columns=keys)
            with pd.ExcelWriter('{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id),
                                engine='xlsxwriter') as writer:
                df[0].to_excel(writer, sheet_name='Messages')
            return ['Log of {} for this guild:'.format(args[2]), '{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id)]

        # Get log of aa specific channell
        if args[1] in {"channel"}:
            for each in message.channel_mentions:
                channel = each.name

            if VERBOSE >= 2:
                print(message.channel, channel)
            select_st = select([Corpus]).where(and_(
                Corpus.c.guild == message.guild.id,
                Corpus.c.channel == channel))
            df = [None]
            with ENGINE.connect() as conn:
                result = conn.execute(select_st).fetchall()
                keys = conn.execute(select_st).keys()

                entries = [each.values() for each in result]
                for each in entries:
                    each[0] = 'id_{}'.format(each[0])
                    each[3] = 'uid_{}'.format(each[3])
                    each[11] = 'mid_{}'.format(each[11])
                    each[13] = 'gid_{}'.format(each[13])

                df[0] = pd.DataFrame(entries, columns=keys)
            with pd.ExcelWriter('{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id),
                                engine='xlsxwriter') as writer:
                df[0].to_excel(writer, sheet_name='Messages')
            return ['Log of {} for this guild:'.format(args[2]), '{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id)]

    else:
        # Get a log of the guild
        if VERBOSE >= 2:
            print('Getting full log...')
        select_st = select([Corpus]).where(
            Corpus.c.guild == message.guild.id)
        df = [None]
        with ENGINE.connect() as conn:
            result = conn.execute(select_st).fetchall()
            if result:
                keys = conn.execute(select_st).keys()

                entries = [each.values() for each in result]
                for each in entries:
                    each[0] = 'id_{}'.format(each[0])
                    each[3] = 'uid_{}'.format(each[3])
                    each[11] = 'mid_{}'.format(each[11])
                    each[13] = 'gid_{}'.format(each[13])

                df[0] = pd.DataFrame(entries, columns=keys)
                with pd.ExcelWriter('{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id), engine='xlsxwriter') as writer:
                    df[0].to_excel(writer, sheet_name='Messages')
                return ['Log of all messages for this guild:', '{}/log/Log_{}.xlsx'.format(DEFAULT_DIR, message.guild.id)]
            else:
                return None


# Placeholder function
def get_help(message):
    """
	Get the help file in ./docs/help for admin command to get a log file
	:param message: <Discord.message object>
	:return: <String> The local help file
	"""
    pass


setup()
