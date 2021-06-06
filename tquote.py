#!/usr/bin/python3

import pendulum
from discord import Embed
import pandas as pd
from sqlalchemy import and_, func, select, MetaData, Table, Column, Integer, String

from tutil import fetch_file, is_admin, increment_usage, fetch_value
from constants import DEFAULT_DIR, ENGINE, VERBOSE, extSet


def setup():
    global meta, Quotes, Lore, Config
    meta = MetaData()
    Config = Table(
        'config', meta,
        Column('id', Integer, primary_key=True),
        Column('guild_name', String),
        Column('locale', String),
        Column('schedule', String),
        Column('quote_format', String),
        Column('lore_format', String),
        Column('url', String),
        Column('qAdd_format', String),
    )
    Quotes = Table(
        'famQuotes', meta,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('text', String),
        Column('date', String),
        Column('guild', String),
        Column('guild_name', String),
        Column('embed', String),
    )
    Lore = Table(
        'famLore', meta,
        Column('id', Integer, primary_key=True),
        Column('name', String),
        Column('text', String),
        Column('date', String),
        Column('guild', String),
        Column('embed', String),
        Column('guild_name', String),
    )
    meta.create_all(ENGINE)
    if VERBOSE >= 0:
        print('[+] End Quotes Setup')


def helper(message):
    """
	Main entry point from main.py, handles majority of argument parsing
	:param message: <Discord.message object>
	:return: <lambda function> Internal function dispatch
	"""

    text = message.content
    for each in message.mentions:
        text = text.replace('<@!{}>'.format(each.id), each.name)
    args = text.split()
    guild = message.guild.id

    # Lore
    if args[0] == '!lore':
        increment_usage(message.guild, 'lore')
        if len(args) > 1:
            if args[1] == 'add' and is_admin(message.author):
                return insert_quote(message, Lore)
            elif args[1] == 'delete' and is_admin(message.author):
                return delete_quote(message.guild.id, args[2])
            elif args[1] == 'help' and is_admin(message.author):
                return get_help(message.author)
            else:
                return get_quote(guild, Lore, ' '.join(args[1:]), True)
        else:
            return get_quote(guild, Lore, None, True)

    # Quote with options
    elif len(args) > 1:
        increment_usage(message.guild, 'quote')
        if args[1] == 'help':
            return get_help(message.author)
        elif args[1] == 'delete' and is_admin(message.author):
            return delete_quote(message.guild.id, args[2])
        elif args[1] == 'log' and is_admin(message.author):
            return get_quote_log(message.guild.id)
        else:
            return get_quote(guild, Quotes, ' '.join(args[1:]), True)

    # Any random quote
    else:
        increment_usage(message.guild, 'quote')
        return get_quote(guild, Quotes, None, True)


def get_quote_log(guild):
    """
	Return an xlsx of all quotes in the guild to the user.
	:param guild:
	:return:
	"""
    df = [None, None]
    for idx, Table in enumerate({Quotes, Lore}):
        select_st = select([Table]).where(
            Table.c.guild == guild)
        with ENGINE.connect() as conn:
            result = conn.execute(select_st).fetchall()
            keys = conn.execute(select_st).keys()

            entries = [each.values() for each in result]
            for each in entries:
                each[0] = 'id_{}'.format(each[0])
                each[4] = 'g_{}'.format(each[4])

            df[idx] = pd.DataFrame(entries, columns=keys)

    with pd.ExcelWriter('{}/log/quoteLog_{}.xlsx'.format(DEFAULT_DIR, guild), engine='xlsxwriter') as writer:
        df[1].to_excel(writer, sheet_name='Sheet_1')
        df[0].to_excel(writer, sheet_name='Sheet_2')
    return ['Log of all quotes and lore for this guild:', '{}/log/quoteLog_{}.xlsx'.format(DEFAULT_DIR, guild)]


def insert_quote(message, Table, adder=None):
    """
	Insert a quote to the database
	:param message: <Discord.message object>
	:param Table: <SQLAlchemy.Table object>
	:param adder: <String> Username of the member who added the :speech_left:
	:return: <String> Notifying of message being added
	"""
    if Table is None:
        Table = Quotes
    config = load_config(message.guild.id)
    if config:
        server_locale = config[2]
        stm = config[7].replace('\\n', '\n')
    else:
        server_locale = 'Asia/Tokyo'
        stm = '--{} on {}'
    # Suppress any user or role mentions
    text = message.content
    for each in message.mentions:
        text = text.replace('<@!{}>'.format(each.id), each.name)
    for each in message.role_mentions:
        text = text.replace('<@&{}>'.format(each.id), each.name)
    text = text.replace('@everyone', '@ everyone')
    text = text.replace('@here', '@ here')

    args = text.split()

    embed = str(message.attachments[0].url) if message.attachments else None
    if not embed:
        embed = ''
        for each in args:
            if each.find('http') != -1:
                if each.split('.')[-1] in extSet['image']:
                    embed = '{}\n{}'.format(embed, each)
    date = pendulum.now(tz=server_locale).to_day_datetime_string()

    with ENGINE.connect() as conn:
        if Table.name == 'famQuotes':
            ins = Table.insert().values(
                id=message.id,
                name=message.author.name,
                text=text,
                date=date,
                guild=str(message.guild.id),
                guild_name=message.guild.name,
                embed=embed,
            )
            conn.execute(ins)

            if not fetch_value(message.guild.id, 10):
                banner = Embed(title="{} Added Quote: {}".format(adder, message.id), description=text)
            else:
                banner = Embed(title="Added Quote: {}".format(message.id), description=text)
            if embed:
                banner.set_image(url=embed)
            banner.set_footer(text=stm.format(message.author.name, date))

        elif Table.name == 'famLore':
            ins = Table.insert().values(
                id=message.id,
                name=args[2],
                text=' '.join(args[3:]),
                date=date,
                guild=str(message.guild.id),
                embed=embed,
                guild_name=message.guild.name,
            )
            conn.execute(ins)

            banner = Embed(title="Added Lore: {}".format(message.id), description=' '.join(args[3:]))
            if embed:
                banner.set_image(url=embed)
            banner.set_footer(text=stm.format(args[2], date))

    return banner


def get_quote(guild, Table, username=None, raw=False):
    """
	Retrieve a quote from the database.
	:param guild: <int> message.guild.id
	:param Table: (Optional) <SQLAlchemy.Table> Quotes or Lore, defaults to Quotes
	:param username: (Optional) <str> Case sensitive Discord username, without discriminator
	"""


    if username:
        select_user = select([Table]).where(and_(
            Table.c.name == username,
            Table.c.guild == guild)).order_by(func.random())
        select_id = select([Table]).where(and_(
            Table.c.id == username,
            Table.c.guild == guild))
    else:
        select_rand = select([Table]).where(
            Table.c.guild == guild).order_by(func.random())

    with ENGINE.connect() as conn:
        if username:
            result = conn.execute(select_id).fetchone()
            if not result:
                result = conn.execute(select_user).fetchone()
        else:
            result = conn.execute(select_rand).fetchone()

        # Result fields translate as
        # [0]: message id, [1]: author, [2]: quote, [3]: date, [6]: embed url
        if result:
            config = load_config(guild)
            if config:
                if Table.name == 'famQuotes':
                    stm = config[4].replace('\\n', '\n')
                    title = "Quote {}".format(result[0])
                elif Table.name == 'famLore':
                    stm = config[5].replace('\\n', '\n')
                    title = "Lore {}".format(result[0])
            else:
                if Table.name == 'famQuotes':
                    stm = '---{} on {}'
                    title = "Quote {}".format(result[0])
                elif Table.name == 'famLore':
                    stm = '---Scribed by the Lore Master {}, on the blessed day of {}'
                    title = "Lore {}".format(result[0])

        if raw:
            # Check if there is an attached img or file to send as well
            if len(result) > 6 and result[6]:
                stm = stm + '\n' + result[6]
            # Result fields translate as
            # [1]: author, [2]: quote, [3]: date, [6]: embed url
            return stm.format(title, result[2], result[1], result[3])

        else:
            stm = stm.format(result[1], result[3])

            banner = Embed(title=title, description=result[2])
            if len(result) > 6 and result[6]:
                banner.set_image(url=result[6])
            banner.set_footer(text=stm)

            return banner


def delete_quote(guild, msg_id):
    """
	Remove a quote from the database
	:param guild: <Int> Discord guild ID
	:param msg_id: <Int> Discord message ID
	:return: <String> Notify if quote has been removed
	"""
    with ENGINE.connect() as conn:
        for Table in {Quotes, Lore}:
            select_st = select([Table]).where(and_(
                Table.c.id == msg_id,
                Table.c.guild == guild
            ))
            try:
                result = conn.execute(select_st).fetchone()
                if result:
                    quote = '{}\n ---{} on {}'.format(result[2], result[1], result[3])

                    ins = Table.delete().where(and_(
                        Table.c.id == msg_id,
                        Table.c.guild == guild
                    ))
                    conn.execute(ins)
                return "Deleted quote: {}".format(quote)
            except Exception as e:
                if VERBOSE >= 1:
                    print('[!] Exception in tquote: {}'.format(e))
                return None


def check_if_exists(guild, msg_id):
    """
	Internal function toeEnsure that we do not add the same message to the database multiple times
	:param guild: <Int> Discord guild ID
	:param msg_id: <Int> Discord message ID
	:return: <Bool>
	"""
    with ENGINE.connect() as conn:
        select_st = select([Quotes]).where(and_(
            Quotes.c.id == msg_id,
            Quotes.c.guild == guild))
        if conn.execute(select_st).fetchall():
            return True
    return False


def load_config(guild):
    """
	Retrieve any formatting options from database
	:param guild: <Int> Discord guild ID
	:return: <List> SQLAlchemy row entry from Config Table
	"""
    result = None
    with ENGINE.connect() as conn:
        select_st = select([Config]).where(Config.c.id == guild)
        result = conn.execute(select_st).fetchone()
    return result


def get_help(author):
    """
	Get the help file in ./docs/help 
	:param message: <Discord.message.author object>
	:return: <String> The local help file
	"""
    text = fetch_file('help', 'quotes')
    if not is_admin(author):
        text = text.split('For Admins:')[0]
    banner = Embed(title='General Help', description=text)
    return banner


setup()
