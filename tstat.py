#!/usr/bin/python3

import re
import sqlite3

from discord import Embed, File
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
import seaborn as sns

from tutil import fetch_file, increment_usage
from constants import PATH_DB, DEFAULT_DIR, STOPWORDS, VERBOSE


def setup(guild, user=None, channel=None):
    global log_df, clean_description, stem_description
    log_df = []
    clean_description = []
    stem_description = []

    with sqlite3.connect(PATH_DB) as conn:
        if user:
            sql_st = 'Select content from corpus where user_name like {} and guild={}'.format(
                '\'' + user + '%\'', guild)
            log_df = pd.read_sql(sql_st, conn)
        elif channel:
            sql_st = 'Select content from corpus where channel like {} and guild={}'.format(
                '\'' + channel + '%\'', guild)
            log_df = pd.read_sql(sql_st, conn)
        else:
            sql_st = 'Select content from corpus where guild={}'.format(guild)
            log_df = pd.read_sql(sql_st, conn)

        log_df['word_count'] = log_df['content'].apply(lambda x: len(str(x).split(" ")))
        normalize_pd_dataframe(log_df.content)
    if VERBOSE >= 0:
        print("[+] Stats setup complete with user={} channel={}".format(user, channel))


def normalize_pd_dataframe(dataframe):
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
        desc = re.sub("'", " ", desc)
        clean_description.append(desc)
    log_df['clean_description'] = clean_description


def lematize_pd_dataframe(dataframe):
    """
	Lemmatize words, such as running --> run
	:param dataframe: <Pandas dataframe>
	:return: <Pandas dataframe>
	"""
    for w in range(len(dataframe)):
        split_text = dataframe[w].split()
        lem = WordNetLemmatizer()
        split_text = [lem.lemmatize(word) for word in split_text if word not in STOPWORDS]
        split_text = " ".join(split_text)
        stem_description.append(split_text)
    return '1'


def helper(message):
    increment_usage(message.guild, 'stats')
    text = message.content

    # We need to flatten user and role mentions in order to properly query the database
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
        banner = word_cloud(' '.join(args[2:]), message.guild.name)
        return banner
    elif operator == 'channel' and len(args) > 2:
        setup(message.guild.id, channel=' '.join(args[2:]))
        banner = word_cloud(' '.join(args[2:]), message.guild.name)
        return banner
    else:
        setup(message.guild.id)

    return {
        'common': lambda: word_frequency(args),
        'cloud': lambda: word_cloud('the server', message.guild.name),
        'count': lambda: word_count(args, message.guild.name),
        'phrases': lambda: get_ngrams(args, message.guild.name),
        'help': lambda: get_help(message),
    }.get(operator, lambda: None)()


def word_frequency(args):
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
        elif limit > 99:
            limit = 99
    freq = pd.Series(' '.join(clean_description).split()).value_counts()[:limit]
    freq = str(freq).split('dtype')[0]

    split_freq = [each.split('\n') for each in freq.split(' ') if each]
    split_freq = [item for sublist in split_freq for item in sublist]

    # Find the longest combination of WORD and FREQ to create appropriate padding for pretty printing
    longest = 0
    for idx in range(0, len(split_freq) - 1):
        if len(split_freq[idx]) + len(split_freq[idx + 1]) > longest:
            longest = len(split_freq[idx]) + len(split_freq[idx + 1]) + 1

    count = 1
    values = ''
    for idx, _ in enumerate(split_freq):
        if idx + 1 == len(split_freq):
            break
        padding = ' '
        prefix = count if count >= 10 else '0{}'.format(count)
        if idx % 2 == 0:
            while len(padding) + len(split_freq[idx]) + len(split_freq[idx + 1]) <= longest:
                padding += ' '
            values += '`{}: {}{}{}`\n'.format(prefix, split_freq[idx], padding, split_freq[idx + 1])
            count += 1

    banner = Embed(title='Word Frequencies')
    banner.add_field(name='The {} most common words for this server are:'.format(limit), value=values)
    return None, banner


def word_count(args, guild):
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

    filename = '{}_wordcount.png'.format(guild)
    plt.savefig("{}/log/stats/{}".format(DEFAULT_DIR, filename))
    plt.clf()

    image = File('{}/log/stats/{}'.format(DEFAULT_DIR, filename), filename=filename)
    banner = Embed(title='Wordcount', description="Number of messages between length {} and {}.".format(low, high))
    banner.set_image(url='attachment://{}'.format(filename))
    return image, banner


def word_cloud(type_, guild):
    """
	Create a word cloude
	:param type_: <String> Either the user, channel, or guild name
	:param guild: <String> Discord guild name
	:return: <List> Strings describing the type_ and filename
	"""
    word_cloud_obj = WordCloud(
        width=800,
        height=800,
        background_color='black',
        stopwords=STOPWORDS,
        max_words=1000,
        min_font_size=20
    ).generate(str(clean_description))

    fig = plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(word_cloud_obj)
    plt.axis('off')

    filename = '{}_wordcloud.png'.format(guild)
    fig.savefig("{}/log/stats/{}".format(DEFAULT_DIR, filename))
    plt.clf()

    image = File('{}/log/stats/{}'.format(DEFAULT_DIR, filename), filename=filename)
    banner = Embed(title='Wordcloud', description="The most common single words for {}.".format(type_))
    banner.set_image(url='attachment://{}'.format(filename))
    return image, banner


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
    ).fit(clean_description)

    bag_of_words = vec.transform(clean_description)
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
    # Validate input arguments
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

    # Plotting
    trigram_df = pd.DataFrame(ngrams)
    trigram_df.columns = ["n-gram", "Freq"]
    sns.set(rc={'figure.figsize': (12, 8)}, font_scale=1)
    bp = sns.barplot(x="n-gram", y="Freq", data=trigram_df)
    bp.set_xticklabels(bp.get_xticklabels(), rotation=75)
    plt.tight_layout()
    plt.axis('on')

    # Cleanup
    filename = "{}_ngram.png".format(guild)
    figure = bp.get_figure()
    figure.savefig('{}/log/stats/{}'.format(DEFAULT_DIR, filename))
    plt.clf()

    image = File('{}/log/stats/{}'.format(DEFAULT_DIR, filename), filename=filename)
    banner = Embed(title='N-Grams',
                   description="The {} most common phrases of length {} to {}.".format(limit, low, high))
    banner.set_image(url='attachment://{}'.format(filename))
    return image, banner


def get_help(message):
    increment_usage(message.guild, 'help')
    banner = Embed(title='Stats Help', description=fetch_file('help', 'stats'))
    return None, banner
