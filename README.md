<p align="center">
  <a href="" rel="noopener">
 <img src="https://i.imgur.com/M3wjra4.png" alt="Bot logo"></a>
</p>

<h3 align="center">Bot Name</h3>

<div align="center">

  ![Status](https://img.shields.io/badge/status-active-success.svg)
  ![Platform](https://img.shields.io/badge/platform-discord-blue.svg)
  ![Language](https://img.shields.io/badge/language-python-yellow.svg)

</div>

---

<p align="center"> 🤖 Few lines describing what your bot does.
    <br> 
</p>

## 📝 Table of Contents
+ [About](#about)
+ [List of Commands](#commandlist)
+ [

## List of Commands <a name = "commandlist"></a>
+ [!help](#!help)
+ [!config](#!config)
+ [!sched](#!sched)
+ [!quote](#!quote)
+ [!lore](#!lore)
+ [!dict](#!dict)
+ [!stats](#!stats)
+ [!8ball](#!8ball)

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

Optional parameters are:
+ !quote [USER] --- Display a quote that was said by that specific user. Note that this is their actual username (case sensitive) and not their display nickname so as to prevent confusion as users change nicknames often. If you are unsure click on the user in either the right panel users list or on their profile picture next to any message they've sent to see their actual username. This does not include the discriminator, which is a # sign folowed by four numbers.
+ !quote help --- Display a brief explanation of the command usage available to the user.


## !lore <a name = "!lore"></a>
  Works almost exactly the same as !quote but new entries can only be added by administrators, a sort of VIP version of !quote or a randomized version of a pinned message.
  
  Aliased names for the command are:
  + !l
  
  Optional parameters are:
  + !lore help --- Display a brief explanation of the command usage available to the user.
  + !lore [USER] --- Display a piece of lore from a specific user.
  + !lore add [USER] [TEXT] --- Add a new lore entry of [TEXT] with the author set as [USER] at the current date and time. Note that the [USER] must be a single word, any text after the first whitespace will be part of [TEXT]. Administrators may add a :x: reaction to the "!lore add" message to remove the entry.
  
## !dict <a name = "!dict"></a>
Returns the English Wiktionary entry for a word or phrase. This does not necessarily need to be an English word, it simply needs to have an entry in the https://en.wiktionary.org site.

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
The classic magic eight ball, now on your Discord.
Use !8ball followed by a question to have your fortune read.

Aliased names for the command are:
+ !8
+ !eight
+ !eightball
