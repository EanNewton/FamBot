#!/usr/bin/python3

import os
import pandas as pd
import sqlite3
from sqlite3 import Error
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
import seaborn as sns
from discordUtils import debug, fetchFile


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), './log/quotes.db')
DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))


def setup(user=None, channel=None):
	global log_df, stop_words, clean_desc, stem_desc
	pd.set_option('display.max_colwidth', None)
	conn = sqlite3.connect(DEFAULT_PATH)
	
	if user:
		sql_st = 'Select content from corpus where user_name like {}'.format('\''+user+'%\'')
		log_df = pd.read_sql(sql_st, conn)
	elif channel:
		sql_st = 'Select content from corpus where channel like {}'.format('\''+channel+'%\'')
		log_df = pd.read_sql(sql_st, conn)
	else:
		log_df = pd.read_sql('Select content from corpus', conn)
	
	log_df['word_count'] = log_df['content'].apply(lambda x: len(str(x).split(" ")))
	stop_words = set(stopwords.words("english"))
	
	#Remove special characters and normalize words
	clean_desc = []
	for w in range(len(log_df.content)):
		desc = log_df['content'][w].lower()
		desc = re.sub('[^a-zA-Z]', ' ', desc)
		desc = re.sub("&lt;/?.*?&gt;", " &lt;&gt ", desc)
		desc = re.sub("`|'", " ", desc)
		clean_desc.append(desc)
		
	log_df['clean_desc'] = clean_desc
	word_frequency = pd.Series(' '.join(log_df['clean_desc']).split()).value_counts()[:30]
	
	add_stopwords = "www http https com youtube ' ` im like watch get got override schedule cc discordapp".split()
	stop_words = stop_words.union(add_stopwords)
	stop_words = stop_words.union([
		"channel cannot", 
		"channel cannot used music", 
		"cannot used music command", 
		"cannot used", 
		"used music", 
		"music command", 
		"channel cannot used", 
		"cannot used music", 
		"used music command", 
		"channel cannot used music command"
	])

	#Lemmatize words, such as running --> run
	stem_desc = []
	for w in range(len(log_df['clean_desc'])):
		split_text = log_df['clean_desc'][w].split()
		lem = WordNetLemmatizer()
		split_text = [lem.lemmatize(word) for word in split_text if not word in stop_words]
		split_text = " ".join(split_text)
		stem_desc.append(split_text)
		
	print("[+] Stats setup complete with user={} channel={}".format(user, channel))

def getFreq(args):
	limit = 10
	if len(args) == 3:
		limit = int(args[2])
	freq = pd.Series(' '.join(stem_desc).split()).value_counts()[:limit]
	freq = str(freq).split('dtype')[0]
	return [None, freq]

def helper(message):
	args = message.content.split()
	operator = 'cloud'
	if len(args) > 1:
		operator = args[1].lower()
	if operator == 'user' and len(args) > 2:
		setup(user=args[2])
		banner = wordCloud(args[2])
		setup()
		return banner
	elif operator == 'channel' and len(args) > 2:
		setup(channel=args[2])
		banner = wordCloud(args[2])
		setup()
		return banner
	return {
		'common': lambda: getFreq(args),
		'cloud': lambda: wordCloud(),
		'count': lambda: wordCount(args),
		'phrases': lambda: get_ngrams(args),
		'update': lambda: setup(),
		'help': lambda: getHelp(),
	}.get(operator, lambda: None)()
	
def wordCount(args):
	if len(args) == 4:
		low = int(args[2])
		high = int(args[3])
		if low > high:
			low, high = high, low
	else:
		low = 1
		high = 20
	if low < 1: low = 1
	if high < 2: high = 2
	if high < low: high = low + 1
	x = log_df['word_count']
	plt.xlabel("Message word length")
	plt.ylabel("# of Messages")
	fig = plt.hist(x, bins='auto', range=(low,high))
	plt.savefig("wordcount.png")
	plt.clf()
	banner = "Number of messages between length {} and {}.".format(str(low), str(high))
	return ["wordcount.png", banner]

def wordCloud(type_='the server'):
	wordcloud = WordCloud(
		width=800, 
		height=800, 
		background_color='black', 
		stopwords=stop_words, 
		max_words=1000, 
		min_font_size=20
	).generate(str(stem_desc))
	fig = plt.figure(figsize=(8,8), facecolor=None)
	plt.imshow(wordcloud)
	plt.axis('off')
	fig.savefig("wordcloud.png")
	plt.clf()
	return ["wordcloud.png", "The most common single words for {}.".format(type_)]

def make_ngrams(low, high, n=None):
	vec = CountVectorizer(ngram_range=(low, high), max_features=20000).fit(stem_desc)
	bag_of_words = vec.transform(stem_desc)
	sum_words = bag_of_words.sum(axis=0)
	words_freq = [(word, sum_words[0, i]) for word, i in vec.vocabulary_.items() if not word in stop_words]
	words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
	return words_freq[:n]

def get_ngrams(args):
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
	if limit < 1: limit = 1
	ngrams = make_ngrams(int(low), int(high), n=int(limit))
	trigram_df = pd.DataFrame(ngrams)
	trigram_df.columns=["Trigram", "Freq"]
	fig = sns.set(rc={'figure.figsize':(12,8)}, font_scale=1)
	bp = sns.barplot(x="Trigram", y="Freq", data=trigram_df)
	bp.set_xticklabels(bp.get_xticklabels(), rotation=75)
	plt.tight_layout()
	plt.axis('on')
	figure = bp.get_figure()
	figure.savefig("ngram.png")
	plt.clf()	
	banner = "The {} most common phrases of length {} to {}.".format(str(limit), str(low), str(high))
	return ["ngram.png", banner]

def getHelp():
	return [None, fetchFile('help', 'stats')]
