#!/usr/bin/python3

import os
import re
import sqlite3
from sqlite3 import Error

import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
import seaborn as sns

from tutil import debug, fetchFile, incrementUsage
from constants import PATH_DB, DEFAULT_DIR, STOPWORDS


def setup(guild, user=None, channel=None):
	global log_df, clean_desc, stem_desc
	clean_desc = []
	stem_desc = []
	
	with sqlite3.connect(PATH_DB) as conn:
		if user:
			sql_st = 'Select content from corpus where user_name like {} and guild={}'.format(
				'\''+user+'%\'', guild)
			log_df = pd.read_sql(sql_st, conn)
		elif channel:
			sql_st = 'Select content from corpus where channel like {} and guild={}'.format(
				'\''+channel+'%\'', guild)
			log_df = pd.read_sql(sql_st, conn)
		else:
			sql_st = 'Select content from corpus where guild={}'.format(guild)
			log_df = pd.read_sql(sql_st, conn)

	log_df['word_count'] = log_df['content'].apply(lambda x: len(str(x).split(" ")))
	getNorm(log_df.content)
	getLem(log_df['clean_desc'])
		
	print("[+] Stats setup complete with user={} channel={}".format(user, channel))


def getNorm(dataframe):
	"""
	Remove special characters and normalize words
	:param dataframe: <Pandas dataframe>
	:return: <Pandas dataframe>
	"""
	for w in range(len(dataframe)):
		desc = log_df['content'][w].lower()
		desc = re.sub('[^a-zA-Z]', ' ', desc)
		desc = re.sub("&lt;/?.*?&gt;", " &lt;&gt ", desc)
		desc = re.sub("`|'", " ", desc)
		clean_desc.append(desc)
	log_df['clean_desc'] = clean_desc


def getLem(dataframe):
	"""
	Lemmatize words, such as running --> run
	:param dataframe: <Pandas dataframe>
	:return: <Pandas dataframe>
	"""
	for w in range(len(dataframe)):
		split_text = dataframe[w].split()
		lem = WordNetLemmatizer()
		split_text = [lem.lemmatize(word) for word in split_text if not word in STOPWORDS]
		split_text = " ".join(split_text)
		stem_desc.append(split_text)


def helper(message):
	incrementUsage(message.guild, 'stats')
	text = message.content

	#We need to flatten user and role mentions in order to properly query the database
	for each in message.mentions:
		text = text.replace('<@!{}>'.format(each.id), each.name)
	for each in message.channel_mentions:
		text = text.replace('<#{}>'.format(each.id), each.name)
	
	args = text.split()
	operator = 'cloud'
	if len(args) > 1:
		operator = args[1].lower()

	if operator == 'user' and len(args) > 2:
		setup(message.guild.id, user=' '.join(args[2:]))
		banner = wordCloud(' '.join(args[2:]), message.guild.name)
		return banner
	elif operator == 'channel' and len(args) > 2:
		setup(message.guild.id, channel=' '.join(args[2:]))
		banner = wordCloud(' '.join(args[2:]), message.guild.name)
		return banner
	else:
		setup(message.guild.id)
	
	return {
		'common': lambda: getFreq(args),
		'cloud': lambda: wordCloud('the server', message.guild.name),
		'count': lambda: wordCount(args, message.guild.name),
		'phrases': lambda: get_ngrams(args, message.guild.name),
		'help': lambda: getHelp(message),
	}.get(operator, lambda: None)()


def getFreq(args):
	"""
	Generate a pandas Series of word frequency pairs
	:param args: <List> user supplied input describing upper limit
	:return: <List> Contains Pandas series of word frequency pairs
	"""
	limit = 10
	if len(args) >= 3:
		limit = int(args[2])
		if limit < 1:
			limit = 1
	freq = pd.Series(' '.join(stem_desc).split()).value_counts()[:limit]
	freq = str(freq).split('dtype')[0]
	return [freq, None]

	
def wordCount(args, guild):
	"""
	Create a bar plot of message lengths
	:param args: <List> user supplied input describing minimum and maximum lengths
	:param guild: <String> Discord guild name
	:return: <List> Strings describing args and filename of graph
	"""
	if len(args) == 4:
		low = int(args[2])
		high = int(args[3])
		if low > high:
			low, high = high, low
	else:
		low = 1
		high = 20
	if low < 1: 
		low = 1
	if high < 2: 
		high = 2
	if high < low: 
		high = low + 1
	
	plt.xlabel("Message word length")
	plt.ylabel("# of Messages")
	plt.hist(log_df['word_count'], bins='auto', range=(low, high))

	plt.savefig("{}_wordcount.png".format(guild))
	plt.clf()

	return [
		"Number of messages between length {} and {}.".format(low, high),
		"{}_wordcount.png".format(guild),
		 ]


def wordCloud(type_, guild):
	"""
	Create a word cloude
	:param type_: <String> Either the user, channel, or guild name
	:param guild: <String> Discord guild name
	:return: <List> Strings describing the type_ and filename
	"""
	wordcloud = WordCloud(
		width=800, 
		height=800, 
		background_color='black', 
		stopwords=STOPWORDS, 
		max_words=1000, 
		min_font_size=20
	).generate(str(stem_desc))
	
	fig = plt.figure(figsize=(8,8), facecolor=None)
	plt.imshow(wordcloud)
	plt.axis('off')

	fig.savefig("{}_wordcloud.png".format(guild))
	plt.clf()

	return [
		"The most common single words for {}.".format(type_),
		"{}_wordcloud.png".format(guild), 
		]


def make_ngrams(low, high, n=None):
	"""
	Internal function to convert corpus into a set of ngrams
	:param low: <Int> Lower ngram length
	:param high: <Int> Upper ngram length
	:return: <List> Sorted ngram frequency list
	"""
	vec = CountVectorizer(
		strip_accents='unicode', 
		ngram_range=(low, high), 
		max_features=20000
		).fit(stem_desc)

	bag_of_words = vec.transform(stem_desc)
	sum_words = bag_of_words.sum(axis=0)

	words_freq = [(word, sum_words[0, i]) for word, i in vec.vocabulary_.items() if not word in STOPWORDS]
	words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)

	return words_freq[:n]


def get_ngrams(args, guild):
	"""
	Create a bar plot of common short phrases within messages
	:param args: <String> User supplied input describing low, high, and limit
	:param guild: <String> Discord guild name
	:return: <List> Strings describing args and filename
	"""
	#Validate input arguments
	if len(args) >= 4:
		low = int(args[2])
		high = int(args[3])
		if low > high:
			low, high = high, low
		if low < 1: low = 1
		if high < 1: high = 1
		if len(args) >= 5:
			limit = int(args[4])
		else:
			limit = 30
	else:
		low = 2
		high = 3	
		limit = 30
	if len(args) == 3:
		limit = int(args[2])
	if limit < 1: 
		limit = 1

	ngrams = make_ngrams(int(low), int(high), n=int(limit))

	#Plotting
	trigram_df = pd.DataFrame(ngrams)
	trigram_df.columns=["n-gram", "Freq"]
	sns.set(rc={'figure.figsize':(12,8)}, font_scale=1)
	bp = sns.barplot(x="n-gram", y="Freq", data=trigram_df)
	bp.set_xticklabels(bp.get_xticklabels(), rotation=75)
	plt.tight_layout()
	plt.axis('on')

	#Cleanup
	figure = bp.get_figure()
	figure.savefig("{}_ngram.png".format(guild))
	plt.clf()	

	return [
		"The {} most common phrases of length {} to {}.".format(limit, low, high),
		"{}_ngram.png".format(guild),
		]


def getHelp(message):
	incrementUsage(message.guild, 'help')
	return [None, fetchFile('help', 'stats')]

