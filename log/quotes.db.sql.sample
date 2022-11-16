BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "famLore" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR,
	"text"	VARCHAR,
	"date"	VARCHAR,
	"guild"	VARCHAR,
	"embed"	VARCHAR,
	"guild_name"	VARCHAR,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "usageCounts" (
	"id"	INTEGER,
	"guild_name"	BLOB,
	"quote"	INTEGER,
	"lore"	INTEGER,
	"wolf"	INTEGER,
	"wotd"	INTEGER,
	"dict"	INTEGER,
	"trans"	INTEGER,
	"google"	INTEGER,
	"config"	INTEGER,
	"sched"	INTEGER,
	"filter"	INTEGER,
	"doip"	INTEGER,
	"gif"	INTEGER,
	"stats"	INTEGER,
	"eight"	INTEGER,
	"help"	INTEGER,
	"raw_messages"	INTEGER,
	"custom"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "commands" (
	"id"	INTEGER,
	"guild_name"	TEXT,
	"name"	TEXT,
	"value"	TEXT,
	"guild_id"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "filters" (
	"id"	integer,
	"level"	TEXT,
	"guild_id"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "config" (
	"id"	INTEGER NOT NULL,
	"guild_name"	VARCHAR,
	"locale"	TEXT,
	"schedule"	VARCHAR,
	"quote_format"	VARCHAR,
	"lore_format"	VARCHAR,
	"url"	VARCHAR,
	"qAdd_format"	VARCHAR,
	"filtered"	VARCHAR,
	"mod_roles"	VARCHAR,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "famQuotes" (
	"id"	integer,
	"name"	TEXT,
	"text"	TEXT,
	"date"	TEXT,
	"guild"	TEXT,
	"guild_name"	TEXT,
	"embed"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "schedule" (
	"id"	integer,
	"name"	TEXT,
	"locale"	TEXT,
	"guild"	TEXT,
	"guild_name"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "corpus" (
	"id"	INTEGER NOT NULL,
	"content"	VARCHAR,
	"user_name"	VARCHAR,
	"user_id"	VARCHAR,
	"time"	VARCHAR,
	"channel"	VARCHAR,
	"embeds"	VARCHAR,
	"attachments"	VARCHAR,
	"mentions"	VARCHAR,
	"channel_mentions"	VARCHAR,
	"role_mentions"	VARCHAR,
	"msg_id"	VARCHAR,
	"reactions"	VARCHAR,
	"guild"	VARCHAR,
	"guild_name"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "riddlesUsers" (
	"id"	integer,
	"name"	TEXT,
	"current"	TEXT,
	"score"	TEXT,
	"solved"	TEXT,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "riddles" (
	"id"	integer,
	"name"	TEXT,
	"text"	TEXT,
	"solution"	TEXT,
	PRIMARY KEY("id")
);
COMMIT;
