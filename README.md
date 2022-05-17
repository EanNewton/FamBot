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


- [📝 Table of Contents](#-table-of-contents)
- [About](#about-a-name--abouta)
- [List of Commands](#list-of-commands-a-name--commandlista)
  - [!help](#help-a-name--helpa)
  - [!config](#config-a-name--configa)
  - [!log](#log-a-name--loga)
  - [!sched](#sched-a-name--scheda)
  - [!quote](#quote-a-name--quotea)
  - [!lore](#lore-a-name--lorea)
  - [!dict](#dict-a-name--dicta)
  - [!stats](#stats-a-name--statsa)
  - [!google](#google-a-name--googlea)
  - [!gif](#gif-a-name--gifa)
  - [!word](#word-a-name--worda)
  - [!yandex](#yandex-a-name--yandexa)
  - [!custom](#custom-a-name--customa)
- [How It Works](#how-it-works)
  - [Architecture](#architecture)
  - [Process Flow](#process-flow)

# About <a name = "about"></a>

I initially created this bot to address a problem I saw occurring frequently: Twitch was helping to connect people from all over the globe, which is a wonderful thing, but it brought the problem of communicating across all those disparate places. A streamer would say something like, "Hey friends! I'll be streaming every Tuesday at 6:00PM!" but when exactly that 6:00PM on Tuesday actually is would be different for people located in London vs New York vs Melbourne. I wanted a simple and intuitive way for anyone to find out when it would occur for them with a single command. 

The project has been growing and adding features as requested since then. If there's a change you'd like to see feel free to issue a Pull Request or contact me.

Or, clone the the project to a local directory and launch it with:
`python3 main.py`
You will need a bot token from the Discord Developer portal as well as one from Wolfram, placed into ./.env

# List of Commands <a name = "commandlist"></a>
+ [!help](#!help)
+ [!config](#!config)
+ [!log](#!log)
+ [!custom](#!custom)
+ [!sched](#!sched)
+ [!quote](#!quote)
+ [!lore](#!lore)
+ [!dict](#!dict)
+ [!stats](#!stats)
+ [!8ball](#!8ball)
+ [!wolfram](#!wolfram)
+ [!google](#!google)
+ [!word](#!word)
+ [!poem](#!poem)
+ [!yandex](#!yandex)


## !help <a name = "!help"></a>
Displays a list of available commands and a brief description of what they do.

**Examples**

![help example](https://github.com/EanNewton/FamBot/blob/master/Samples/help.png)

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
    "Quote Added Format": "\"{0}\"\n by {1} on {2}",
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

## !log <a name = "!log"></a>
Admin command to get a log of all messages sent in the guild in Excel format.
Note: This will be sent to the channel the command was used in and therefore available to any users who can see the channel.

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
+ !sched override [CONTINENT]/[CITY] @User1 @User2 @User3... --- an administrator only command to change any user's location

**Examples**

![sched exmaple](https://github.com/EanNewton/FamBot/blob/master/Samples/sched.png)

## !quote <a name = "!quote"></a>
Users can react to any message in the discord with the :speech_left: reaction to add it to a list of quotes. 
Quotes may be any message that is not from a bot, including text, images, videos, embeds, or files.
A random quote can then be displayed by using the !quote command.
Administrators can use :x: on a message that has a received a :speech_left: to remove it from the quotes list. Multiple users reacting with :speech_left: will not add the quote multiple times.

Aliased names for the command are:
+ !q
+ !quote

Optional parameters are:
+ !quote [USER] --- Display a quote that was said by that specific user. You can either use @user or their username format. Note that this is their actual username (case sensitive) and not their display nickname so as to prevent confusion as users change nicknames often. If you are unsure click on the user in either the right panel users list or on their profile picture next to any message they've sent to see their actual username. This does not include the discriminator, which is a # sign folowed by four numbers.
+ !quote [ID] --- Display a specific quote by its ID number.
+ !quote help --- Display a brief explanation of the command usage available to the user.
+ !quote log --- Admin command to return a log of all saved quotes in Excel format. Note: This is posted to the channel the command is used in and therefore available to any users who can view that channel.
+ !quote delete [ID] --- Admin command to remove a quote by its ID number.

**Examples**

![quote example](https://github.com/EanNewton/FamBot/blob/master/Samples/quote.png)

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
Returns the English Wiktionary entry for a word or phrase. This does not necessarily need to be an English word, it simply needs to have an entry in the https://en.wiktionary.org site. Due to Discord's character limit for Embed objects, words with very long entries may not return anything.

Aliased names for the command are:
+ !dict
+ !dictionary
+ !wiki
+ !wiktionary

Optional parameters are:
+ !dict [TEXT] --- Display an explanation of any single word or phrase.
+ !dict help --- Show all available web interfaced commands.

**Example**
> !dict baseball
![dict example](https://github.com/EanNewton/FamBot/blob/master/Samples/dict.png)

## !stats <a name = "!stats"></a>
Display some fun info about the messages being sent. The default command will generate a word cloud of the most common words for the server.

Optional parameters are:
+ !stats help --- Show the help interface.
+ !stats user [USERNAME] --- Create a word cloud for the specified user. Like !quote this is the case sensitive version of the username without the discriminator.
+ !stats channel [CHANNEL] --- Create a word cloud for the specified channel. This is provided as the #channel-name tag.
+ !stats count [LOW] [HIGH] --- Create a bar graph showing the number of messages of length between LOW and HIGH.
+ !stats phrases [LOW] [HIGH] [LIMIT] --- Create a graph showing the most common phrases / n-grams of length between LOW and HIGH. LIMIT is the amount of n-grams to display.
+ !stats common [LIMIT] --- Create a textual list of the most common single words for the server, up to LIMIT.

**Examples**
>!stats
---
![stats default](https://raw.githubusercontent.com/EanNewton/FamBot/master/Samples/stats.png)
---

>!stats user
---
![stats user](https://github.com/EanNewton/FamBot/blob/master/Samples/stats%20user.png)
---

>!stats channel
---
![stats channel](https://github.com/EanNewton/FamBot/blob/master/Samples/stats%20channel.png)
---

>!stats count 2 20
---
![stats count](https://github.com/EanNewton/FamBot/blob/master/Samples/stats%20count.png)
---

>!stats phrases 2 5 10
---
![stats phrases](https://github.com/EanNewton/FamBot/blob/master/Samples/stats%20phrases.png)
---

>!stats common 10
---
![stats common](https://github.com/EanNewton/FamBot/blob/master/Samples/stats%20common.png)
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

Optional parameters are:
+ !wolf txt [QUERY] --- Query the Wolfram Alpha engine for QUERY and return a text based response.
+ !wolf img [QUERY] --- Query the Wolfram Alpha engine for QUERY and return an image based response.

Aliased names for the command are:
+ !w
+ !wolf
+ !wolfram

**Examples**
>!wolf img Evaluate ∫4x6−2x3+7x−4dx
---
![wolf example 1](https://github.com/EanNewton/FamBot/blob/master/Samples/wolfimg.png)

![wolf example 1 result](https://github.com/EanNewton/FamBot/blob/master/Samples/762496307855491113.gif)

---
>!wolf txt what is the weather in Tokyo
---
![wolf  example 2](https://github.com/EanNewton/FamBot/blob/master/Samples/wolftxt.png)
---

## !google <a name = "!google"></a>
Did someone ask a question that could have been Googled? Send a link to Let Me Google That For You for them.

Aliased names for the command are:
+ !g
+ !google
+ !lmgtfy

**Examples**
> !google what is a banana
---
`https://lmgtfy.com/?q=what+is+a+banana&iie=1`

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

![word example](https://github.com/EanNewton/FamBot/blob/master/Samples/word.png)

## !yandex <a name = "!yandex"></a>
Return a link to a reverse image search.

Aliased names for the command are:
+ !yandex
+ !tineye
+ !image
+ !reverse

Optional parameters are:
+ !yandex [URL] --- Given a URL to an image return a link to a reverse image search for the provided image. You can right click an image within Discord and choose Copy Link.

## !custom <a name = "!custom"></a>
Add custom commands to your discord.
Admins can react to any message with :gear: to add a new command. The first word of the message will be the command name, the remainder will be what is displayed. The command name is taken literally so if you want a ! or . or any prefix make sure to include that.
Admins can react to any message :X: to remove a command where the first word matches a command name to remove it.
Custom commands can override built-in commands, so if you want to disable any command -- such as !sched or !quote -- simply set up a custom command with the same name.

Custom commands can be nested and can also contain specific additional parameters.
For example, if you add the command `!custom1 Foo` and then add `!custom2 <custom1> Bar <GUILD>`, calling !custom2 will then display `Foo Bar my server`. Make sure that nested command calls are enclosed in `<>`. Custom commands do not suppress user, channel, or role mentions and will ping people if you include a mention in them.

Use `!custom` to display the help text as well as any custom commands you have setup for your server.

Additional Parameters include:
+ `<URL>` --- The URL from your from your !config file
+ `<NOW>` or `<TIME>` ---  The current time for the server location from your !config file
+ `<LOCALE>` or `<LOCATION>` --- The server locale from your !config file
+ `<AUTHOR>` --- The username of whoever used the command
+ `<GUILD>` --- Your Discord guild name
+ `<SCHED>` --- Calls !sched
+ `<QUOTE>` --- Calls !quote
+ `<LORE>` --- Calls !lore
	

**Examples**

![custom example](https://github.com/EanNewton/FamBot/blob/master/Samples/custom.png)

---

![custom help](https://github.com/EanNewton/FamBot/blob/master/Samples/custom-help.png)



# How It Works

----

## Architecture

The core architecture of the bot is a series of Python files hooked into a SQLite database via SQLalchemy. In order to support modularity and unpredictable future extensions it was decided on to store and pull help files and the like from editable server side files stored in plain text format, to transfer configuration files as XML.

## Process Flow

### On Boot

1. We provide the discord.py API with our Discord Developer API secret token from a .env file and establish a connection to the Discord servers.

2. The core boot initialization is started via the various modules' import statements. With each one that has database access calling a custom `setup` function to notify the SQLalchemy engine of the Tables and metadata it will need. An example of these `setup` functions may look like:

   ```python
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
           Column('context', String),
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
   ```

3. We then notify the logging system and local user that the bot is ready to go along with its current version, which guilds it is active in, and their member counts.

### Joining a Server

Upon joining a new Discord server the bot kicks off an initialization process. 

This init process consists of:

1. Notify the local log system of the request.

2. Query the database to see if the Discord guild has an existing config saved or not. 

   1. If so, update it based on new parameters.

   2. If not, generate a new config with default sample parameters and insert it to the database via `config_create_default`. Return and recursively call `config_create` to confirm these new values are stored and recognized. The default config values look like:

      ```python
          with ENGINE.connect() as conn:
              ins = Config.insert().values(
                  id=guild.id,
                  guild_name=guild.name,
                  locale='Asia/Tokyo',
                  schedule='0=10,17:15;1=10,12;2=16,10:15;3=2:44;4=10;5=16:30;',
                  quote_format='{0}\n ---{1} on {2}',
                  lore_format='{0}\n ---Scribed by the Lore Master {1}, on the blessed day of {2}',
                  url='Come hang with us at: <https://www.twitch.tv/>',
                  qAdd_format='Added:\n "{0}"\n by {1} on {2}',
                  filtered='none',
                  mod_roles='mod;admin;discord mod;',
                  anonymous=1,
                  timer_channel=0,
              )
      ```

3. Send the Owner of the guild a DM with a welcome message.

4. Recall the database initialization for quotes and meta utility via `tquote.setup` and `tutil.setup`. The bot is now ready for action!

### Taking Commands

Once the bot is up and running it actively monitors for two types of events -- users sending messages and users reaction to messages with an emoji -- and asynchronously handles them.

When a new message is detected:

1. The bot calls `on_message` and passes off the raw message data to the `dispatch`  fucntion of `switchboard.py` for processing.
2. `dispatch` first does some pre-processing:
   1. It checks if the message author was bot and if so ignores it to prevent recursive commands from spiraling out of control.
   2. It increments a database counter for the number of raw messages it has seen.
   3. It then splits the raw object data up into usable chunks and looks to see what it contains, as well as prepares a `set` data structure for its own reply. Finally notifying the log of the raw input and its contents.
   4. We then check if the user is requesting a command they custom uploaded for their server. If not, we check for the command symbol `$` at the start of the message and run the command through a custom spell-check autocorrect to attempt to repair any minor typos. (More on how the Spell Checker works below.)
3. If everything looks good we then compare the request to a list of known commands, call the relevant module's function, and return the requested information to the user as a new message in the Discord guild.

When an emoji reaction is detected:

1. We look and see if it is a 🗨, ❌, or ⚙.
2. 🗨 is a request to add a new quote. We check the message's unique ID to see if it has already been added, if so we log and silently fail, if not we pass it off to `tquote.py`'s `insert_quote` function add it to the database.
3. ❌ is a request to delete an existing quote. After verifying that both the quoted message exists in the database and that the requesting user has a Discord role tagged as a moderator or admin role, and finally remove the entry from the database. If not, we log and silently fail. 
4. ⚙ is a request to add a new custom command for the guild. After verifying that the requesting user has an administrative role we download any attached images or files, generate a local filesystem URI for said file, and insert the new command to a database table with the first word being the new command's calling name and any remaining text after the first whitespace as raw text to return on calling the command. We then update a `dict` data structure to notify the bot of the new command without having to reinitialize the entire project.

### Spell Checker

The nature of an active online chat program is that there will be many diverse users typing quickly who cannot be expected to memorize every command and even if they do there will frequently be typos. Having a command request fail when the user expects it to work is frustrating for them. To address this I have implemented an auto correct system.

We first establish some constants for a number of different alphabets and their related regex sets. This `constants.py` module consists simply of:

```python
# -*- coding: utf-8 -*-

word_regexes = {
    'cmd': r'[A-Za-z]+',
    'en': r'[A-Za-z]+',
    'pl': r'[A-Za-zęĘóÓąĄśŚłŁżŻźŹćĆńŃ]+',
    'ru': r'[АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя]+',
    'uk': r'[АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬЮюЯя]+',
    'tr': r'[a-zA-ZçÇğĞüÜöÖşŞıİ]+',
}

alphabets = {
    'cmd': 'abcdefghijklmnopqrstuvwxyz1234567890',
    'en': 'abcdefghijklmnopqrstuvwxyz',
    'pl': 'abcdefghijklmnopqrstuvwxyzęóąśłżźćń',
    'ru': 'шиюынжсяплзухтвкйеобмцьёгдщэарчфъ',
    'uk': 'фагксщроємшплуьцнжхїйювязтибґідеч',
    'tr': 'abcçdefgğhıijklmnoöprsştuüvyzqwxÇĞİÜÖ',
}
```

This is paired with a JSON file stored in a compressed archive of word lists for each alphabet paired with their common frequency counts in that language (based on the archives of Project Gutenberg) in order to determine how likely a word from the user's raw input is versus known words, and if the likelyhood is significant we iteratively replace it.

For example, the first ten lines of the English word frequency dictionary are:

```json
    "Sir": 27,
    "Arthur": 26,
    "Conan": 4,
    "Doyle": 4,
    "in": 19136,
    "our": 921,
    "series": 83,
    "by": 6217,
    "laws": 209,
    "are": 3389,
```

We implement the itertools library to slice each given word and recursively check for a number of frequent types of misspellings. Namely:

1. Deletes -- "th" -> "the"
2. Transposes -- "teh" -> "the"
3. Replaces -- "tge" -> "the"
4. Inserts -- "thwe" -> "the"

The actual iteration over words is run as:

```python
class Speller:
    def __init__(self, lang='en', threshold=0, nlp_data=None):
        self.threshold = threshold
        self.nlp_data = load_from_json(lang) if nlp_data is None else nlp_data
        self.lang = lang

        if threshold > 0:
            print('Original number of words: {}'
                  .format(len(self.nlp_data)))
            self.nlp_data = {k: v for k, v in self.nlp_data.items()
                             if v >= threshold}
            print('After applying threshold: {}'
                  .format(len(self.nlp_data)))

    def existing(self, words):
        """{'the', 'teh'} => {'the'}"""
        return set(word for word in words
                   if word in self.nlp_data)

    def autocorrect_word(self, word):
        """most likely correction for everything up to a double typo"""
        def get_candidates(word):
            w = Word(word, self.lang)
            candidates = (self.existing([word]) or
                          self.existing(w.typos()) or
                          self.existing(w.double_typos()) or
                          [word])
            return [(self.nlp_data.get(c, 0), c) for c in candidates]

        candidates = get_candidates(word)

        # in case the word is capitalized
        if word[0].isupper():
            decapitalized = word[0].lower() + word[1:]
            candidates += get_candidates(decapitalized)

        best_word = max(candidates)[1]

        if word[0].isupper():
            best_word = best_word[0].upper() + best_word[1:]
        return best_word

    def autocorrect_sentence(self, sentence):
        return re.sub(word_regexes[self.lang],
                      lambda match: self.autocorrect_word(match.group(0)),
                      sentence)

    __call__ = autocorrect_sentence
    
class Word(object):
    """container for word-based methods"""
    __slots__ = ['slices', 'word', 'alphabet']  # optimization
   
    def __init__(self, word, lang='en'):
        """
        Generate slices to assist with typo
        definitions.

        'the' => (('', 'the'), ('t', 'he'),
                  ('th', 'e'), ('the', ''))

        """
        slice_range = range(len(word) + 1)
        self.slices = tuple((word[:i], word[i:])
                            for i in slice_range)
        self.word = word
        self.alphabet = alphabets[lang]
        
 # ... Clipped

    def typos(self):
        """letter combinations one typo away from word"""
        return chain(self._deletes(),
                     self._transposes(),
                     self._replaces(),
                     self._inserts())

    def double_typos(self):
        """letter combinations two typos away from word"""
        return chain.from_iterable(
            Word(e1).typos() for e1 in self.typos())
```



