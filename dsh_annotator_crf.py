import sklearn
import scipy.stats
from sklearn.metrics import make_scorer
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RandomizedSearchCV

import sklearn_crfsuite
from sklearn_crfsuite import scorers
from sklearn_crfsuite import metrics

from itertools import chain

from spacy.tokens import Token

import os
import pickle
import re

import matplotlib.pyplot as plt
plt.style.use('ggplot')


SPACY_ATTRIBUTES = []
LABEL = ['conll_pos']
DEFAULT_ATTR_VALUE = False


class CorpusLoader:
    def __int__(self):
        self.set_custom_attributes(['DSH'])

    def set_custom_attributes(self, attributes):
        for attr in attributes:
            Token.set_extension(attr, default=DEFAULT_ATTR_VALUE, force=True)

    # return a dictionary of features for a token excluding the label
    def token2features(self, token):
        return {attr: val for (attr, val) in token.items() if attr in SPACY_ATTRIBUTES}

    # return a list of features for the tokens in the sentence excluding the target label
    def sentence2features(self, sentence):
        return [self.token2features(token) for token in sentence]

    # return a list of labels for the tokens in the sentence
    def sentence2label(self, sentence):
        return [token.get(LABEL[0], 'O') for token in sentence]

    def load_file(self, path):
        print('-- Loading file: ' + path)
        sentences = pickle.load(open(path, 'rb'))

        sentences_as_features = []

        for sentence in sentences:
            sentence_as_features = self.sentence2features(sentence)
            sentence_as_features.append(sentence_as_features)

        return sentences_as_features

    def load_train_corpus(self, path):
        print('Loading training corpus from: ' + path)
        file_list = [file for file in os.listdir(path) if file.endswith('.tml') and re.search('test', file) is None]

        train_corpus = []

        for file in file_list:
            pin = os.path.join(path, file)
            train_corpus += self.load_file(pin)

        return train_corpus
