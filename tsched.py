#!/usr/bin/python3
import discord
import pendulum
from discord import Embed
from sqlalchemy import select, MetaData, Table, Column, Integer, String

from tutil import fetch_file, is_admin, increment_usage, debug
from constants import VERBOSE, TZ_ABBRS, ENGINE, help_general


def setup():
	global meta, Users, Config
	meta = MetaData()
	Users = Table(
		'schedule', meta,
		Column('id', Integer, primary_key=True),
		Column('name', String),
		Column('locale', String),
		Column('guild', String),
		Column('guild_name', String),
	)
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
		Column('timer_channel', String),
	)
	meta.create_all(ENGINE)
	if VERBOSE >= 0:
		print('[+] End Schedule Setup')


def helper(message: discord.Message, op_override=None):
	"""
	Main entry point from main.py
	:param op_override: Activate a specific operator
	:param message: <Discord.message object>
	:return: <lambda function> Internal function dispatch
	"""

	args = message.content.split()
	ops = {'get', 'set', 'help', 'override', 'next'}

	operator = 'get'
	if len(args) > 1 and args[1] in ops:
		operator = args[1]
	if op_override:
		operator = op_override

	return {
		'get': lambda: get_schedule(message),
		'set': lambda: set_schedule(message),
		'help': lambda: get_help(message),
		'override': lambda: override(message),
		'next': lambda: get_schedule(message, True),
	}.get(operator, lambda: None)()


# TODO this is a terribly long and confusing function,
# TODO consider rewriting it
def get_schedule(message: discord.Message, raw=False) -> discord.Embed:
	"""
	Return next scheduled event
	:param raw: True = return only next event
	:param message: <discord.Message>
	:return: <discord.Embed>
	"""

	config = load_config(message.guild.id)
	if config:
		guild_name = config[1]
		server_locale = config[2]
		locale = server_locale
		dt = pendulum.now(tz=server_locale)
		schedule_raw_str = config[3]
		days = schedule_raw_str.split(';')
		hours = [day.split('=') for day in days]
		schedule = []
		scheduled_times = []
		dict_ = {}

		# Process the config from SQL into a set of times
		for each in hours:
			if each[0] != '' and each[1] != '':
				if each[0] != ' ' and each[1] != ' ':
					dict_[int(each[0])] = each[1].split(',')
		for each in dict_.items():
			for hour in each[1]:
				if ':' in hour:
					hour = hour.split(':')
				if hour != '' and hour != ' ':
					scheduled_times.append(hour)
			schedule.append(pendulum.now(tz=server_locale).add(days=each[0]))

		# Get only the time diff for the next event
		if raw:
			if dt.day_of_week != pendulum.MONDAY:
				diff = None
				while diff is not None or "a few seconds ago" not in diff:
					for day in range(len(schedule)):
						if isinstance(scheduled_times[day], list):
							# Contains minutes
							schedule[day] = schedule[day].at(
								int(scheduled_times[day][0]), int(scheduled_times[day][1]))
						else:
							schedule[day] = schedule[day].at(int(scheduled_times[day]))
					diff = schedule[0].diff_for_humans()

			banner = Embed(title='Schedule for {}'.format(guild_name))
			banner.add_field(name="Next event {}.".format(diff), value="Join us!")
			return banner

		# Get the full schedule
		else:
			banner = Embed(title='Schedule for {}'.format(guild_name))
			dt_local_name = dt.timezone.name
			now_in_server = pendulum.now(tz=server_locale)
			url = config[6]

			if not message.author.bot:
				args = message.content.split()
				if len(args) > 1:
					# User requested specific location
					locale = TZ_ABBRS.get(args[1].lower(), args[1])
				else:
					# Checking for saved locale in DB
					user = get_user(message.author.id)
					if user:
						locale = user[2]

			# Needed for handling partial weeks, ie so we don't post a message with only 1 or 2 days
			schedule_duplicate = schedule.copy()
			# Show current server time vs current user time
			user_time = '{} in {}\n'.format(dt.to_day_datetime_string(), locale)
			server_time = '{} in {}'.format(now_in_server.to_day_datetime_string(), server_locale)
			banner.add_field(name='Local Time', value=user_time)
			banner.add_field(name='Remote Time', value=server_time)

			while schedule[0].day_of_week != pendulum.MONDAY:
				for day in range(len(schedule)):
					schedule[day] = schedule[day].add(days=1)

			schedule.pop(0)
			formatted_schedule = ''

			# Previous / Current Week
			if now_in_server.day_of_week != pendulum.MONDAY:
				# Get us to Monday
				while schedule_duplicate[0].day_of_week != pendulum.MONDAY:
					for day in range(len(schedule_duplicate)):
						schedule_duplicate[day] = schedule_duplicate[day].add(days=-1)

				#schedule_duplicate.pop(0)
				for day in range(len(schedule_duplicate)):
					if isinstance(scheduled_times[day], list):
						# Contains minutes
						schedule_duplicate[day] = schedule_duplicate[day].at(
							int(scheduled_times[day][0]), int(scheduled_times[day][1]))
					else:
						schedule_duplicate[day] = schedule_duplicate[day].at(int(scheduled_times[day]))

					# Convert timezone and add to message
					schedule_duplicate[day] = schedule_duplicate[day].in_tz(locale)
					if schedule_duplicate[day].format('DDDD') >= dt.format('DDDD'):
						if schedule_duplicate[day].format('DDDD') == dt.format('DDDD'):
							formatted_schedule += '**{}**\n'.format(schedule_duplicate[day].to_day_datetime_string())
						else:
							formatted_schedule += '{}\n'.format(schedule_duplicate[day].to_day_datetime_string())

			# Next Week
			for day in range(len(schedule)):
				if isinstance(scheduled_times[day], list):
					# Contains minutes
					schedule[day] = schedule[day].at(
						int(scheduled_times[day][0]), int(scheduled_times[day][1]))
				else:
					schedule[day] = schedule[day].at(int(scheduled_times[day]))
				# Convert timezone and add to message
				schedule[day] = schedule[day].in_tz(locale)
				if schedule[day].format('DDDD') == dt.format('DDDD'):
					formatted_schedule += '**{}**\n'.format(schedule[day].to_day_datetime_string())
				else:
					formatted_schedule += '{}\n'.format(schedule[day].to_day_datetime_string())

			banner.add_field(name='Schedule', value=formatted_schedule, inline=False)
			banner.add_field(name='URL', value=url, inline=False)
			banner.add_field(name='Help support this bot!', value='All donations go to development and server costs.',
							 inline=False)
			banner.add_field(name='PayPal', value=help_general['paypal'])
			banner.add_field(name='Invite the bot to your server.', value=help_general['invite'], inline=False)
			banner.set_footer(text='Use `!schedule help` for more information.')
			return banner


async def override(message: discord.Message) -> discord.Embed:
	"""
	Admin command to manually change a user's saved location
	:param message: <Discord.message object> Describing which users to change to which locations
	:return: <String> Describing if the users' location was set or updated successfully
	"""
	increment_usage(message.guild, 'sched')
	if await is_admin(message.author, message):
		banner = Embed(title='Schedule Override', description='Change a user\'s location.')
		args = message.content.split()
		# Args should translate as: 1 id, 2 name, 3 locale
		if len(args) < 4:
			banner.add_field(
				name='Invalid syntax.',
				value='Formatting is: `!schedule override [TIMEZONE] @USER` you may mention any number of users.'
			)

		else:
			locale = TZ_ABBRS.get(args[2].lower(), args[2])
			success = [[], []]

			for each in message.mentions:
				user = get_user(int(each.id))

				if user:
					with ENGINE.connect() as conn:
						query = Users.update().where(Users.c.id == each.id).values(locale=locale)
						conn.execute(query)

					if VERBOSE >= 2:
						print('[+] {} UPDATED LOCALE TO {} FOR USER {}'.format(
							message.author, locale, each.name))
					success[0].append('Changed {} to: {}'.format(each.name, locale))

				else:
					insert_user(each.id, message.guild, each.name, locale)
					if VERBOSE >= 2:
						print('[+] {} SETTING {}\'s SCHEDULE TO: {}'.format(
							message.author, each.name, locale))
					success[1].append('Set {} to: {}'.format(each.name, locale))
			banner.add_field(name='Updated schedule location.', value='\n'.join(success[0]))
			banner.add_field(name='Created schedule location.', value='\n'.join(success[1]))
		return banner


def set_schedule(message: discord.Message) -> discord.Embed:
	"""
	User command to set their locale
	:param message: <Discord.message object> Describing where to set location to
	:return: <String> Describing new location for user
	"""
	increment_usage(message.guild, 'sched')
	args = message.content.split()
	config = load_config(message.guild.id)
	banner = Embed(title='Schedule')

	if config:
		server_locale = config[2]
	else:
		server_locale = 'Asia/Tokyo'

	# if no location provided default to server locale
	# if server has no locale default to Tokyo
	# if there is no server locale the schedule will not be displayed
	# however this allows users to still get their locations set
	locale = server_locale if len(args) < 3 else TZ_ABBRS.get(args[2].lower(), args[2])
	user = get_user(message.author.id)
	old_locale = user[2]
	if user:
		with ENGINE.connect() as conn:
			query = Users.update().where(
				Users.c.id == message.author.id,
			).values(locale=locale)
			conn.execute(query)
		banner.add_field(name='Updated your schedule location.', value='From: {}\nTo: {}'.format(old_locale, locale))
	else:
		insert_user(message.author.id, message.guild, message.author.name, locale)
		banner.add_field(name='Set your schedule location.', value='To: {}'.format(locale))
	return banner


def insert_user(id_: int, guild_: discord.guild, name: str, locale: str) -> None:
	"""
	Internal function to set values in database for a single user
	:param id_: <Int> User ID
	:param guild_: <Discord.guild object>
	:param name: <String> Username
	:param locale: <String> New location for the user
	:return: <None>
	"""

	with ENGINE.connect() as conn:
		ins = Users.insert().values(
			id=id_,
			name=name,
			locale=locale,
			guild=guild_.id,
			guild_name=guild_.name,
		)
		conn.execute(ins)


def get_user(id_: int) -> (None, list):
	"""
	Internal function to get values from database for a single user
	:param id_: <Int> User ID
	:return: <List> SQLAlchemy row result from database
	"""

	with ENGINE.connect() as conn:
		select_st = select([Users]).where(
			Users.c.id == id_, )
		res = conn.execute(select_st)
		result = res.fetchone()
	if result:
		return result


def load_config(guild: int) -> list:
	"""
	Internal function to get Guild configuration data for schedule formatting and default locale
	:param guild: <Int> Discord guild ID
	:return: <List> SQLAlchemy row result from database
	"""
	with ENGINE.connect() as conn:
		select_st = select([Config]).where(Config.c.id == guild)
		res = conn.execute(select_st)
		result = res.fetchone()
	if result:
		return result


async def get_help(message: discord.Message) -> discord.Embed:
	"""
	Get the command help file from ./docs/help
	:param message: <Discord.message object>
	:return: <String> Containing help for the user's available options or list of locations
	"""
	increment_usage(message.guild, 'help')
	args = message.content.split()
	banner = Embed(title='Schedule')

	if len(args) < 3:
		# Get general help
		raw = fetch_file('help', 'schedule')
		if not await is_admin(message.author, message):
			raw = raw.split('For Admins:')[0]
		banner.add_field(name='Help', value=raw)
	else:
		# Get list of cities or continents
		raw = fetch_file('locales', args[2].lower())
		banner.add_field(name='Locales in {}'.format((args[2].lower())), value=raw)

	return banner

# Register with SQLAlchemy on import
setup()
