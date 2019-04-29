# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 15:44:07 2018

@author: ABittar
"""

import spacy
import sys

from resources.token_sequence_rules import RULES
from spacy.matcher import Matcher
from spacy.tokens import Token


# This is an ad hoc workaround to avoid trying to overwrite default attributes
# TODO Find a better, cleaner solution
DEFAULT_ATTRIBUTES = ['DEP', 'HEAD', 'IS_ALPHA', 'IS_ASCII', 'IS_BRACKET', 
                      'IS_CURRENCY', 'IS_DIGIT', 'IS_LEFT_PUNCT', 'IS_LOWER',
                      'IS_OOV', 'IS_PUNCT', 'IS_QUOTE', 'IS_RIGHT_PUNCT',
                      'IS_SPACE', 'IS_STOP', 'IS_TITLE', 'IS_UPPER', 'LEMMA',
                      'LENGTH', 'LIKE_EMAIL', 'LIKE_NUM', 'LIKE_URL', 'LOWER',
                      'ORTH', 'POS', 'PREFIX', 'SENT_START', 'SHAPE', 'SUFFIX',
                      'TAG']


class TokenSequenceAnnotator(object):

    def __init__(self, nlp, verbose=False):
        self.name = 'token_sequence_annotator'
        self.nlp = nlp
        self.matcher = None
        self.matches = []
        self.rules = RULES
        self.verbose = verbose

    def __call__(self, doc):
        """
        :param doc: the current spaCy document object
        :return: the matches
        """
        for rule in self.rules:
            pattern = rule['pattern']
            name = rule['name']
            avm = rule['avm']
            merge = rule.get('merge', False)

            self.matcher = Matcher(self.nlp.vocab)  # Need to do this for each rule separately unfortunately
            self.matcher.add(name, None, pattern)

            matches = self.matcher(doc)
            self.matches.append((rule, matches))
            self.add_annotation(doc, matches, avm, merge)

            if self.verbose:
                print('-- ' + name + ': ' + str(len(matches)) + ' matches.', file=sys.stderr)
        
        return doc
    
    def load_rules(self):
        # TODO this is where we need to parse the rule file - specify path as an argument
        pass

    def add_annotation(self, doc, matches, rule_avm, merge):
        """
        Add annotations to the specified tokens in a match.
        Does not work with operators.
        :param doc: the spaCy document object
        :param matches: the matches
        :param rule_avm: the attribute-value pair dictionary specified in the annotation rule
        :return: None
        """
        for match in matches:
            start = match[1]
            end = match[2]
            span = doc[start:end] # why was this end + 1?
            for j in range(len(span)):
                if j in rule_avm.keys():
                    new_annotations = rule_avm.get(j, None)
                    if new_annotations is not None:
                        for new_attr in new_annotations:
                            token = span[j]
                            val = new_annotations[new_attr]
                            if new_attr in DEFAULT_ATTRIBUTES:
                                # TODO check if modification of built-in attributes is possible
                                print('-- Warning: cannot modify built-in attribute', new_attr, file=sys.stderr)
                            else:
                                token._.set(new_attr, val)
            if merge:
                if self.verbose:
                    print('-- Merging span:', [token for token in span], file=sys.stderr)
                span.merge()

    def print_spans(self, doc):
        s = '\n'
        s += '{:<10}{:<10}{:<10}{:<10}{:<10}'.format('INDEX', 'WORD', 'LEMMA', 'POS1', 'POS2')

        cext = set()        
        for a in doc.user_data:
            cext.add(a[1])

        cext = sorted(cext)

        for a in cext:
            s += '{:<10}'.format(a)

        s += '\n'

        s += '{:<10}{:<10}{:<10}{:<10}{:<10}'.format('-----', '----', '-----', '----', '----')

        for a in cext:
            s += '{:<10}'.format('-' * len(a))

        print(s, file=sys.stderr)
        
        for token in doc:
            s = '{:<10}{:<10}{:<10}{:<10}{:<10}'.format(token.i, token.text, token.lemma_, token.tag_, token.pos_)
            for a in cext:
                val = token._.get(a)
                s += '{:10}'.format(val or '_')
            print(s, file=sys.stderr)


if __name__ == '__main__':
    nlp = spacy.load('en')

    text = 'This self-harm has not been done by Elizabeth Callaghan who cut her arm and cut her legs. I will be very very very happy. I have apple and banana'

    tsa = TokenSequenceAnnotator(nlp)
    nlp.add_pipe(tsa)
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names, file=sys.stderr)
    tsa.print_spans(doc)
