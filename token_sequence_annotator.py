# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 15:44:07 2018

@author: ABittar
"""

import spacy
import sys

from spacy.matcher import Matcher
from spacy.tokens import Token


class TokenSequenceAnnotator(object):

    def __init__(self, nlp):
        self.name = 'token_sequence_annotator'
        self.nlp = nlp
        self.matcher = None
        self.matches = []
        self.rules = self.load_rules()

    def __call__(self, doc):
        """
        :param doc: the current spaCy document object
        :return: the matches
        """
        for rule in self.rules:
            pattern = rule['pattern']
            name = rule['name']
            avm = rule['avm']

            self.matcher = Matcher(self.nlp.vocab) # Need to do this for each rule separately unfortunately
            self.matcher.add(name, None, pattern)

            matches = self.matcher(doc)
            self.matches.append((rule, matches))
            self.add_annotation(doc, matches, avm)

            print('-- ' + name + ': ' + str(len(matches)) + ' matches.', file=sys.stderr)
        
        return doc
    
    def load_rules(self):
        # TODO this is where we need to parse the rule file - specify path as an argument
        print('-- Loading rules')
        
        rules = []
        rules.append({
                'name': 'RULE_1',
                'pattern': [{'LEMMA': 'elizabeth'}, {'LEMMA': 'callaghan'}],
                'avm': {0: {'TSA': 'LIZ', 'TSA': 'FIRST_NAME'}, 1: {'TSA': 'CALLA', 'TSA': 'SURNAME'}}
                })
        rules.append({
                'name': 'RULE_2',
                'pattern': [{'LEMMA': 'have'}, {'LEMMA': 'not'}, {'POS': 'VERB'}],
                'avm': {0: {'TSA': 'NEG'}, 2: {'TSA': 'NEG'}}
                })
        rules.append({
                'name': 'RULE_3',
                'pattern': [{'TSA': 'NEG'}],
                'avm': {0: {'WA': 'TSA', 'LEMMA': 'gohu'}}
                })
        
        # Declare (custom) attributes specified in each rule of the rule file
        for rule in rules:
            avm = rule['avm']
            for token_id in avm:
                for attr in avm[token_id]:
                    attr_int = self.nlp.vocab.strings[attr]
                    print('attr:', attr, attr_int)
                    if not Token.has_extension(attr):
                        # TODO also make sure this is not a standard token attribute, e.g. LEMMA or POS
                        Token.set_extension(attr, default=False)
                        print('-- Added custom attribute', attr, file=sys.stderr)
                    else:
                        print('-- Attribute', attr, 'exists. Skipping.', file=sys.stderr)
        
        return rules
    
    def add_annotation(self, doc, matches, rule_avm):
        """
        Add annotations to the specified tokens in a match
        :param doc: the spaCy document object
        :param matches: the matches
        :param rule_avm: the attribute-value pair dictionary specified in the annotation rule
        :return: None
        """
        for match in matches:
            start = match[1]
            end = match[2]
            span = doc[start:end]
            for j in range(len(span)):
                if j in rule_avm.keys():
                    new_annotations = rule_avm.get(j, None)
                    if new_annotations is not None:
                        for new_attr in new_annotations:
                            token = doc[start:end][j]
                            token._.set(new_attr, new_annotations[new_attr])

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

    text = 'This has not been done by Elizabeth Callaghan.'

    tsa = TokenSequenceAnnotator(nlp)
    nlp.add_pipe(tsa)
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names, file=sys.stderr)
    tsa.print_spans(doc)