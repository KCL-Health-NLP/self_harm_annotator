# -*- coding: utf-8 -*-
"""
    Detokenizer
    
    This is a spaCy pipeline component to modify default tokenization.
    New tokenization rules are specified in an external resource file. These 
    rules are loaded when the component is added to the pipeline and applied 
    when the pipeline is executed.
"""

import os
import spacy
import sys

from spacy.symbols import LEMMA, LOWER, ORTH, POS, TAG


class Detokenizer(object):
    """
    Detokenizer
    
    Detokenize a text according to a set of specified rules.
    """
    
    def __init__(self, nlp):
        """
        Create a new Detokenizer instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
        """
        self.nlp = nlp

    def load_detokenization_rules(self, path, verbose=False):
        """
        Load rules to undo tokenization.
        
        Arguments:
            - path: str; the path to the rule file
            - verbose: bool; print all messages
        
        Return:
            - self.nlp: spaCy Lang; the loaded spaCy piepline object with added detokenization rules
        """
        lines = [line.split('\t') for line in open(path, 'r').read().split('\n') if not line.startswith('#') and line != '']

        for line in lines:
            
            if len(line) != 4:
                raise ValueError('  -- Error: syntax error in detokenisation grammar at ', line)

            rule = {ORTH: line[0], LEMMA: line[1]}

            if line[2] != '_':
                rule[TAG] = line[2]

            if line[3] != '_':
                rule[POS] = line[3]

            if verbose:
                print('  -- Added detokenization rule: ' + str(rule), file=sys.stderr)

            self.nlp.tokenizer.add_special_case(line[0], [rule])

        print('  -- Added ' + str(len(lines)) + ' tokenization rules.', file=sys.stderr)
        
        return self.nlp


if __name__ == '__main__':
    nlp = spacy.load('en_core_web_sm')
    
    text = 'Evidence of self-harm'
    
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
