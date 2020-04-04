Features

Schedule

Uses a combination of a SQLite database and the Pendulum time library to convert a set schedule to a user's local time anywhere in the world.
Commands include:
!schedule to pull up the schedule for the user's saved location or the default location with an additional help tip of they have not set location yet.
!schedule set [location] to set the author's default location.
!schedule help to get the full help read out.
!schedule override [username] [user id] [location] allows a server admin to manually set any users location.
!schedule clear YES to completely erase the schedule database. Requires server admin privileges.

Quotes

Uses a flat table in a SQLite database to store and retrieve quotes from users.
Any user can react to a message with the assigned emote (default is :speech_bubble_left:) to add the message to the database.
The channel filter (see below) will prevent any offensive content from being added.
Likewise, server admins can remove a message manually by reacting with :X:.
By default it will not allow attachments such as embedded videos or images to be added but does allow URLs.

Commands include:
!quote [user] pulls up a random quote, if the user variable is designated will pull up a random quote from that user.
!quote help to get the full help read out.
!quote clear YES to completely erase the quote database. Requires server admin privileges.

Filter

A fully customizable content filter that operates on a per channel basis.
By default server admins are exempted from the filter.
Pulls the filtered words from line separated text files.
Does not perform substring searches or string manipulation to avoid the Scunthorpe problem.
If the filter is triggered it will send a customizable message warning the user to watch their language.
This filtering system was designed to be lenient and pro-free speech. 
Filter commands are only usable by server admins.

Commands include:
!filter set [0, 1, 2, 3] corresponding to off, low, high, and custom. Applies only to channel it is used in.
!filter get to get the filter level of the current channel.
!filter add [level] [phrase] adds the phrase to filters of the corresponding level (1 to 3).
!filter help to get the full help read out.
!filter clear to remove all filter settings.

Riddles

A module making use of two SQLite tables, one to store the riddles and one to store information for each user.
Users can challenge each other to solve fun riddles. 
Comes with a scoring system, requirement that all solutions be spoiler tagged, and ability to upload new riddles.

Commands include:

!riddle get [current] to get a new riddle from the database. If the current option is supplied it will display the most recent riddle given to that user.
!riddle solve [riddle id] ||[solution]|| attempt to solve a riddle.
!riddle add [title]: [text] ||[solution]|| add a new riddle to the database. Special attention should be given that the formatting is correct, the colon and spoiler tags are necessary.
!riddle delete [riddle id] remove the designated riddle. Requires server admin privileges.
!riddle clear YES erase the entire riddle database. Requires server admin privileges.
!riddle help to display the full help read out.
