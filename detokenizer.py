# -*- coding: utf-8 -*-
"""
Created on Fri Aug 17 13:09:54 2018

@author: ABittar
"""

import os
import spacy
import sys

from spacy.symbols import LEMMA, ORTH, POS, TAG


class Detokenizer(object):
    def __init__(self, nlp):
        self.nlp = nlp
           
    def load_detokenization_rules(self, path, verbose=False):
        """
        Load rules to undo tokenization.
        :param path: the path to the rule file
        :return: None
        """
        lines = [line.split('\t') for line in open(path, 'r').read().split('\n') if not line.startswith('#') and line != '']

        for line in lines:
            assert len(line) == 4

            rule = {ORTH: line[0], LEMMA: line[1]}

            if line[2] != '_':
                rule[TAG] = line[2]

            if line[3] != '_':
                rule[POS] = line[3]

            if verbose:
                print('-- Added detokenization rule: ' + str(rule), file=sys.stderr)

            self.nlp.tokenizer.add_special_case(line[0], [rule])

        print('-- Added ' + str(len(lines)) + ' tokenization rules.', file=sys.stderr)
        
        return self.nlp


if __name__ == '__main__':
    nlp = spacy.load('en')
    
    text = 'This is a start-up.'
    
    doc = nlp(text)

    print('ORIGINAL TOKENISATION')
    print('---------------------')

    for token in doc:
        string = '{:<5}{:<15}{:<15}{:<15}{:<15}{:<15}'.format(token.i, token.text, token.lemma_, token.tag_, token.head.i, token.dep_)
        print(string)
    
    tok_rules_path = os.path.join('resources', 'detokenization_rules.txt')
    dtk = Detokenizer(nlp)
    nlp = dtk.load_detokenization_rules(tok_rules_path)
    
    doc2 = nlp(text)
    
    print('CORRECTED TOKENISATION')
    print('---------------------')
    
    for token in doc2:
        string = '{:<5}{:<15}{:<15}{:<15}{:<15}{:<15}'.format(token.i, token.text, token.lemma_, token.tag_, token.head.i, token.dep_)
        print(string)