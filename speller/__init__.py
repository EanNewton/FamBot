import json
import os
import re
import sys
import tarfile
import textwrap
from contextlib import closing

from autocorrect.constants import word_regexes
from autocorrect.typos import Word

PATH = os.path.abspath(os.path.dirname(__file__))


def load_from_tar(lang, file_name='word_count.json'):
    archive_name = os.path.join(PATH, 'data/{}.tar.gz'.format(lang))

    if lang not in word_regexes:
        supported_langs = ', '.join(word_regexes.keys())
        raise NotImplementedError(
            textwrap.dedent("""
            language '{}' not supported
            supported languages: {}
            you can easily add new languages by following instructions at
            https://github.com/fsondej/autocorrect/tree/master#adding-new-languages
            """.format(lang, supported_langs)))

    with closing(tarfile.open(archive_name, 'r:gz')) as tarf:
        with closing(tarf.extractfile(file_name)) as file:
            return json.load(file)


class Speller:
    def __init__(self, lang='en', threshold=0, nlp_data=None):
        self.threshold = threshold
        self.nlp_data = load_from_tar(lang) if nlp_data is None else nlp_data
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


# for backward compatibility
class LazySpeller:
    def __init__(self):
        self.speller = None

    def __call__(self, sentence):
        print('autocorrect.spell is deprecated, \
            use autocorrect.Speller instead')
        if self.speller is None:
            self.speller = Speller()
        return self.speller(sentence)


spell = LazySpeller()
