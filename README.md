<p align="center">
  <a href="" rel="noopener">
 <img src="https://i.imgur.com/M3wjra4.png" alt="Tangerine Bot logo"></a>
</p>

<h3 align="center">Tangerine Bot</h3>

<div align="center">

  ![Status](https://img.shields.io/badge/status-active-success.svg)
  ![Platform](https://img.shields.io/badge/platform-discord-blue.svg)
  ![Language](https://img.shields.io/badge/language-python-yellow.svg)
  ![License](https://img.shields.io/badge/license-GNU%20GPL%20v3-green)

</div>

---

# 📝 Table of Contents
+ [About](#about)
+ [List of Commands](#commandlist)
+ [Info for Geeks](#geeky)

# About <a name = "about"></a>

I initially created this bot to address a problem I saw occurring frequently: Twitch was helping to connect people from all over the globe, which is a wonderful thing, but it brought the problem of communicating across all those disparate places. A streamer would say something like, "Hey friends! I'll be streaming every Tuesday at 6:00PM!" but when exactly that 6:00PM on Tuesday actually is would be different for people located in London vs New York vs Melbourne. I wanted a simple and intuitive way for anyone to find out when it would occur for them with a single command. The project has been growing and adding features as requested since then.

Invite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot

Or, clone the the project to a local directory and launch it with:
`pipenv run python3 main.py`

# List of Commands <a name = "commandlist"></a>
+ [!help](#!help)
+ [!config](#!config)
+ [!sched](#!sched)
+ [!quote](#!quote)
+ [!lore](#!lore)
+ [!dict](#!dict)
+ [!stats](#!stats)
+ [!8ball](#!8ball)
+ [!wolfram](#!wolfram)
+ [!google](#!google)


## !help <a name = "!help"></a>
Displays a list of available commands and a brief description of what they do.

## !config <a name = "!config"></a>
Generates a config file in JSON format. Only usable by the server owner and roles designated as server administrators. Simply edit the file as you desire and then drag and drop it back into any channel in your discord to apply the changes. 

Optional parameters are: 
+ !config reset --- return to a default configuration

**Example Config File**
```
{
    "Server ID": 012340123401234,
    "Server Name": "My First Server",
    "Server Locale": "Asia/Tokyo",
    "Schedule": "Monday = 10; Tuesday = 10; Wednesday = 16; Friday = 10; Saturday = 16; ",
    "URL Footer": "Come hang with us at: <https://www.twitch.tv/>",
    "Quote Format": "{0}\n ---{1} on {2}",
    "Quote Added Format": "Added:\n \"{0}\"\n by {1} on {2}",
    "Lore Format": "{0}\n ---Scribed by the Lore Master {1}, on the blessed day of {2}",
    "Blacklisted Words": "none, one, two foo bar; three",
    "Moderator Roles": "mod;admin;discord mod;\n"
}


To edit your server configuration simply change the appropiate values, and drag and drop it back into Discord to upload. 

You can always use `!config reset` to return to default values.

Server Locale: This is your default timezone location. 
    See "!schedule help" for more locations.
    
Schedule: This is your stream schedule, times are in 24 hour format. 
    The format to add a stream is:
        [DAY] = [TIME 1], [TIME 2];
        Monday = 10:30, 14; Wednesday = 18; Friday = 12:15, 14:30
    This would add scheduled times for Monday at 10:30AM and 2:00PM, Wednesday at 6PM, etc.

URL Footer: A brief message to be displayed beneath the schedule.
        
Quote Format: How quotes should be displayed when a user enters "!quote". 
    To create a line break use \n.
    {0} will be the quote text.
    {1} will be the quote's author.
    {2} will be the date.
    Each {} field may only be used once.
    
Lore Format: How lore should be displayed when a user enters "!lore". 
    Lore works the same as quotes but only admins and mods may add to it. 
    This is useful for stream point redeems. 
    See "!lore help" for more information.
    
Quote Added Format: What is displayed when a user reacts with :speech_left: to add a new quote. 
    It also follows the {} order of text, author, date.
```

## !sched <a name = "!sched"></a>
Display a schedule of upcoming events for the server in the user's own time zone. Any events occurring today will be bolded.

Aliased names for the command are:
+ !s
+ !sched
+ !schedule

Optional parameters are:
+ !sched help --- display more detailed options available to the user
+ !sched help [CONTINENT] --- display a list of cities in that continent that users can set their location to. Continents include: Africa, America, Antarctica, Asia, Atlantic, Australia, Europe, Indian, Pacific, and abbr. Note: "abbr" is a short list of common locations that have been aliased, e.g. pst, est, jst, gmt
+ !sched set [CONTINENT]/[CITY] --- sets the user's timezone to the correct one for that location
+ !sched [CONTINENT]/[CITY] --- see the schedule for that location without changing the user's location
+ !sched override [USER ID] [USER NAME] [CONTINENT]/[CITY] --- an administrator only command to change any user's location

**Example Output**
```
Sat, Sep 5, 2020 11:41 AM in America/Phoenix
Sun, Sep 6, 2020 3:41 AM in Asia/Tokyo
<<>><<>><<>><<>><<>><<>><<>><<>><<>>
**Sat, Sep 5, 2020 12:00 AM**
Sun, Sep 6, 2020 6:00 PM
Mon, Sep 7, 2020 6:00 PM
Wed, Sep 9, 2020 12:00 AM
Thu, Sep 10, 2020 6:00 PM
Sat, Sep 12, 2020 12:00 AM
<<>><<>><<>><<>><<>><<>><<>><<>><<>>
Come hang with us at: https://www.twitch.tv/
<<>><<>><<>><<>><<>><<>><<>><<>><<>>
Help pay for server costs: https://www.patreon.com/tangerinebot
Invite the bot to your server: https://discord.com/api/oauth2/authorize?client_id=663696399862595584&permissions=8&scope=bot
Use !schedule help for more information.
```
## !quote <a name = "!quote"></a>
Users can react to any message in the discord with the :speech_left: reaction to add it to a list of quotes. 
Quotes may be any message that is not from a bot, including text, images, videos, embeds, or files.
A random quote can then be displayed by using the !quote command.
Administrators can use :x: on a message that has a received a :speech_left: to remove it from the quotes list. Multiple users reacting with :speech_left: will not add the quote multiple times.
  
Aliased names for the command are:
+ !q
+ !quote

Optional parameters are:
+ !quote [USER] --- Display a quote that was said by that specific user. Note that this is their actual username (case sensitive) and not their display nickname so as to prevent confusion as users change nicknames often. If you are unsure click on the user in either the right panel users list or on their profile picture next to any message they've sent to see their actual username. This does not include the discriminator, which is a # sign folowed by four numbers.
+ !quote help --- Display a brief explanation of the command usage available to the user.


## !lore <a name = "!lore"></a>
  Works almost exactly the same as !quote but new entries can only be added by administrators, a sort of VIP version of !quote or a randomized version of a pinned message.
  
  Aliased names for the command are:
  + !l
  + !lore
  
  Optional parameters are:
  + !lore help --- Display a brief explanation of the command usage available to the user.
  + !lore [USER] --- Display a piece of lore from a specific user.
  + !lore add [USER] [TEXT] --- Add a new lore entry of [TEXT] with the author set as [USER] at the current date and time. Note that the [USER] must be a single word, any text after the first whitespace will be part of [TEXT]. Administrators may add a :x: reaction to the "!lore add" message to remove the entry.
  
## !dict <a name = "!dict"></a>
Returns the English Wiktionary entry for a word or phrase. This does not necessarily need to be an English word, it simply needs to have an entry in the https://en.wiktionary.org site.

Aliased names for the command are:
+ !dict
+ !dictionary

Optional parameters are:
+ !dict [TEXT] --- Display an explanation of any single word or phrase.

**Example**
> !dict computer
```
noun 
Etymology
From compute +‎ -er.

Definitions
computer (plural computers) 
(now rare, chiefly historical) A person employed to perform computations; one who computes. [from 17th c.] 
(by restriction, chiefly historical) A male computer, where the female computer is called a computress. 
A programmable electronic device that performs mathematical calculations and logical operations, especially one that can process, store and retrieve large amounts of data very quickly; now especially, a small one for personal or home use employed for manipulating text or graphics, accessing the Internet, or playing games or media. [from 20th c.] 
Related Words
See also Thesaurus:computer, 
computation, compute, computing, 
Examples
By which manner of ſpeaking, this Propheteſs, who is ſo exact a Computer, would have us, I ſuppoſe, to conclude, that it would be a great miſtake to think that the number of Angels was either 9, or 11 for one of Men. 
Only a few years ago Mr. Powers, an American computer, disproved a hypothesis about prime numbers which had held the field for more than 250 years. 
One Harvard computer, Annie Jump Cannon, used her repetitive acquaintance with the stars to devise a system of stellar classifications so practical that it is still in use today. 
Hyponym: computress 
Synonyms: processor, 'puter , box , machine, calculator 
Hyponyms: desktop, laptop, portable computer, stored-program computer 
Pronunciation
(UK) IPA: /kəmˈpjuːtə/, /kəmˈpjuːʔə/ 
(US) IPA: /kəmˈpjutɚ/, [kəmˈpʰjuɾɚ] 
Hyphenation: com‧put‧er 
Rhymes: -uːtə(r) 
https://upload.wikimedia.org/wikipedia/commons/5/5c/En-uk-computer.ogg 
https://upload.wikimedia.org/wikipedia/commons/a/a1/En-us-computer.ogg

```
## !stats <a name = "!stats"></a>
Display some fun info about the messages being sent. The default command will generate a word cloud of the most common words for the server.

Optional parameters are:
+ !stats user [USERNAME] --- Create a word cloud for the specified user. Like !quote this is the case sensitive version of the username without the discriminator.
+ !stats channel [CHANNEL] --- Create a word cloud for the specified channel. This is provided as the #channel-name tag.
+ !stats count [LOW] [HIGH] --- Create a bar graph showing the number of messages of length between LOW and HIGH.
+ !stats phrases [LOW] [HIGH] [LIMIT] --- Create a graph showing the most common phrases / n-grams of length between LOW and HIGH. LIMIT is the amount of n-grams to display.
+ !stats common [LIMIT] --- Create a textual list of the most common single words for the server, up to LIMIT.

**Examples**
>!stats
---
![stats default](https://i.imgur.com/RtQR9kJ.png)
---

>!stats user
---
![stats user](https://i.imgur.com/YNXJUy0.png)
---

>!stats channel
---
![stats channel](https://i.imgur.com/Fi7RRRy.png)
---

>!stats count 2 20
---
![stats count](https://i.imgur.com/lgu9Z3U.png)
---

>!stats phrases 2 5 10
---
![stats phrases](https://i.imgur.com/PcEZXSZ.png)
---

>!stats common 10
---
![stats common](https://i.imgur.com/AkxHHUD.png)
---

## !8ball <a name = "!8ball"></a>
The classic 1950's magic eight ball by Carter and Bookman, now on your Discord. 
Use !8ball followed by a question to have your fortune read.

Aliased names for the command are:
+ !8
+ !8ball
+ !eight
+ !eightball

Possible responses are:
+ It is certain.
+ It is decidely so.
+ Without a doubt.
+ Yes -- definitely.
+ You may rely on it.
+ As I see it, yes.
+ Most likely.
+ Outlook good.
+ Yes.
+ Signs point to yes.
+ Reply hazy, try again.
+ Ask again later.
+ Better not tell you now.
+ Cannot predict now.
+ Concentrate and ask again.
+ Don't count on it.
+ My reply is no.
+ My sources say no.
+ Outlook not so good.
+ Very doubtful.

## !wolfram <a name = "!8ball"></a>
Query the Wolfram computational intelligence engine.

Aliased names for the command are:
+ !w
+ !wolf
+ !wolfram

**Examples**
>!wolf Evaluate ∫4x6−2x3+7x−4dx
---
![wolf example 1](https://i.imgur.com/aDZOwK4.png)
---
>!wolf Canada healthcare expenditures
---
![wolf  example 2](https://i.imgur.com/RIgUbvR.png)
---

## !google <a name = "!google"></a>
Did someone ask a question that could have been Googled? Send a link to the Google search for a phrase.

Aliased names for the command are:
+ !g
+ !google
+ !lmgtfy

**Examples**
> !google Evaluate ∫4x6−2x3+7x−4dx
---
`https://google.com/search?q=Evaluate+%E2%88%AB4x6%E2%88%922x3+7x%E2%88%924dx`

## !gif <a name = "!gif"></a>
Display a random gif or add a new one.

Aliased names for the command are:
+ !gif
+ !react
+ !meme

Optional Parameters include:
+ !gif add --- Drag and drop a gif to add it to the possible responses when !gif is used.
+ !gif add nsfw --- Same as `!gif add` but marks it as NSFW.
+ !gif nsfw --- Include gifs marked as NSFW in possible responses.

## !word <a name = "!word"></a>
Get the Word of the Day from https://wordsmith.org/words/today.html

Aliased names for the command are:
+ !word
+ !wotd

**Examples**
```
origami
PRONUNCIATION:
(or-i-GAH-mee)
MEANING:
noun:
1. The art of folding paper into various shapes.
2. An object made by folding paper.
ETYMOLOGY:
 From Japanese origami, from ori (fold) + kami (paper). Earliest
documented use: 1948.
NOTES:
Origami is not just folding paper cranes. Aliaksei Zholner has built a
working V8 engine with just paper and gray matter: video (3 min.). I bow in his general direction. Origami has practical
applications too. For example, in a folding airbag in a car to a solar-panel
array on a satellite.
USAGE:
“But tasting exposes origami folds of scents and flavors.”
Andrew Ross; At The Garrison, ‘Thoughtful’ Food You Won’t Soon Forget;
Portland Press Herald (Maine); Nov 10, 2019.
“A toothy man in dungarees grinned back at me. Slim sort, with a face
creased in a thousand places, like an unfolded bit of origami.”
Dot Gumbi; The Pirates of Maryland Point; 2016.
See more usage examples of origami in Vocabulary.com’s dictionary.
```
# Info for Geeks <a name = "geeky"></a>

This project is written entirely in Python 3 as a passion project, as well as my first project in Python. You are encouraged to use, modify, fork, contribute, hack, or do whatever your heart desires with it within the confines of the GNU General Public License Version 3. Pull requests are warmly welcomed.

The core design philosophies for the project are that it should be: easy to use, easy to maintain and modify, and reliable. Python may not always have the comparable speed of C or its compatriots but I'll be damned if it isn't beautiful.

+ [Packages](#packages)
+ [A Note on Users](#users)
+ [How it Works](#workings)

## Packages <a name = "packages"></a>
The backend makes heavy use of SQLite 3 via the SQLAlchemy project to keep with the Reliable philosophy.

The full list of external Python packages directly imported is:
+ [Pendulum](https://pendulum.eustace.io/)
+ [Discord](https://pythondiscord.com/)
+ [DotEnv](https://github.com/theskumar/python-dotenv)
+ [SQLAlchemy](https://www.sqlalchemy.org/)
+ [AIOHTTP](https://docs.aiohttp.org/en/stable/)
+ [AIOFiles](https://github.com/Tinche/aiofiles)
+ [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
+ [WiktionaryParser](https://github.com/Suyash458/WiktionaryParser)
+ [Pandas](https://pandas.pydata.org/)
+ [NLTK](https://www.nltk.org/)
+ [word_cloud](https://github.com/amueller/word_cloud)
+ [PyPlot](https://matplotlib.org/)
+ [SciKit-learn](https://scikit-learn.org/stable/)
+ [Seaborn](https://seaborn.pydata.org/)

Native imports are:
+ from os import getenv, listdir, path, walk
+ from pathlib import Path
+ from urllib.parse import quote_plus
+ import random
+ import re
+ import sqlite3
+ import json
+ import functools

## A Note on Users <a name = "users"></a>

I feel it is important to remember that software is made to be used. Often there is a disconnect between what the developer sees when they make it and what the users see when they actually use it. As makers it is our duty to bridge that gap the best we can.

One of the first things I noticed when having people test out the bot was that they had trouble remembering exactly *what* the commands are, or how to spell them. I have implemented two ways of combating these problems. 

The first and simplest is to alias the commands. For example, if a user wants to get the definition for a word they should be able to enter `!dictionary`, `!dict`, `!definition`, or `!def` with the same end result. Python makes this simple with the use of hash tables and is done as:
`elif args[0] in {'!8ball', '!8', '!eightball', '!eight'}:`

The second part took a little more doing, that is, how to handle what to do when a user forgets how exactly to spell "dictionary". This was a problem I was seeing frequently (but not only) from users whose first language wasn't my own, and whose language's spelling conventions didn't mesh with the often times odd rules of English. Those users would be trying something like `!dikt`, `!deph`, or `!dektionary`. The solution was to implement a basic form of auto-correct, like you might find on your phone. The actual code for this is located in the ./speller/ directory and is a stripped down and modified version of Filip Sondej's project [autocorrect](https://github.com/fsondej/autocorrect). Filip's code is a work of art and I encourage you to peruse it. It works by making clever use of Python's concept of arrays, iterables, permutations, and generators, alongside regular expressions. It takes textual input, splits it into individual words, generates many variations of those words with array slices, and then compares them to a custom built dictionary of word frequency pairs to find the most likely candidate for what the word should be before then reforming and returning the corrected text.

## How it Works <a name = "workings"></a>

The general top-level work flow of the bot is very straight forward. It first loads its API tokens for Discord and Wolfram from the local .env file, creates generic connections to the local SQLite database, sets up a local log file to keep track of any errors, and then connects to Discord's servers.

It then watches for a handful of events: 
+ [being invited to a new guild](#join)
+ [a reaction being added to a message](#reaction)
+ [an error](#errors)
+ [or a message being sent](#messages)

### On Joining a Guild <a name = "join"></a>

When the bot joins a guild for the first time we want to hit that first design philosophy and Make Things Easy. So, we send a title image and a welcome message.

There are several events that occur frequently with slight variations, e.g. reading from a file or checking if a user is an administrator. For these common tasks I have created the `tutil.py` file. 

Here we will encounter the call to fetchFile() in tutil.py for the first time of many. This function looks into our ./docs/ directory for a given file in a given directory and simply returns it to be used in our banner. Any time the bot will be displaying content to the end users I refer to it as a banner. I implemented it this way as part of the second core philosophy, Easy to Modify, so that these common messages can be changed on the fly without needing to interrupt service to users by stopping and reloading the entire bot to change internal code. 

```
@bot.event
async def on_guild_join(guild):
	banner = 'Hello {}! \n{}'.format(guild.owner.mention, fetchFile('help', 'welcome'))
	await guild.system_channel.send(banner, file=discord.File('./docs/header.png'))
```
--->
```
def fetchFile(directory, filename):
	with open('{}/docs/{}/{}.txt'.format(DEFAULT_DIR, directory, filename), 'r') as f:
		return f.read()
```

This message is sent to the guild's system_channel (by default the first text channel created, though in practice it is often changed by users to a hidden admin channel) and prompts the server owner through basic config setup for the bot.

### On Reactions Added <a name = "reaction"></a>

There are two related instances of when we want the bot to notice a user has added a reaction to a message and take action: to add a new quote, and to remove an existing quote. The Python Discord API provides two similar events for this, on_reaction_add and on_raw_reaction_add, the important difference for us is that the latter allows for users to add messages that were posted at any point in time, even before the bot was added to the server, to the quotes database. This does however mean that we need to fetch the message rather than operating directly with it.

A few additional considerations (that were added after a series of 'interesting' events) are to ensure that the message that is being added was not posted by a bot, that the message is not already in the database, and that the message does not contain any phrases blacklisted by the server (unless the author was themself an administrator). This became the following the code snippet:

```
@bot.event
async def on_raw_reaction_add(payload): 
	channel = bot.get_channel(payload.channel_id)
	message = await channel.fetch_message(payload.message_id)
	
	#Add a quote
	if str(payload.emoji) == '🗨️' and not message.author.bot:
		if not tquote.checkExists(message.guild.id, message.id):
			if not tfilter.check(message) or is_admin(payload.member):
				await message.channel.send(tquote.insertQuote(None, message))
	
	#Remove a quote
	if str(payload.emoji) == '❌'and is_admin(payload.member): 
		await message.channel.send(tquote.deleteQuote(message.guild.id, message.id))
```

Another lesson that was quickly learned from this was the need to suppress @user and @role mentions, but to do so without stripping the context of the original message. This is done via a standard string match and replace operation before sending it off to the database. From tquote.py:

```
def insertQuote(Table, message):
...
	text = message.content
	for each in message.mentions:
		text = text.replace('<@!{}>'.format(each.id), each.name)
	for each in message.role_mentions:
		text = text.replace('<@&{}>'.format(each.id), each.name)
...
```

### On Error <a name = "errors"></a>

This aspect is handled entirely by Python's built in `import logging` and PyDiscord's `on_error`. It was important while trying to locate the nitpicky problems users were running into.

```
@bot.event 
async def on_error(event, *args, **kwargs):
	with open('./log/err.log', 'a') as f:
		if event == 'on_message':
			timestamp = pendulum.now(tz='America/Phoenix').to_datetime_string()
			print(timestamp)
			print('[!] Error in: {}; {}'.format(args[0].channel.name, args[0].guild.name))
			print('[!] Error content: {}'.format(args[0].content))
			print('[!] Error author: {}'.format(args[0].author))
			f.write(f'{timestamp}\nUnhandled message:\n{args[0]}\n\n')
		else:
			raise
			
			
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='./log/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)	
```

However, during development simple logging was not enough to fully diagnose most issues. For this I turned to Python's decorator functions and dropped a wrapper into tutil.py. Placing `@debug` above any function definition prints out to the terminal what function is being called and its arguments before actually entering into the function, and what that function is returning before breaking back into its parent. A sort of refined stack trace if you will. This looks like:

```
def debug(func):
    """Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        print(f"Calling {func.__name__}({signature})\n")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}\n")
        return value
    return wrapper_debug
```

### On Message <a name = "messages"></a>
