# -*- coding: utf-8 -*-
"""
    Token Sequence Annotator
    
    This is a spaCy pipeline component that loads token sequence annotation
    rules specified in an external grammar file (Python script the is imported).
    Rules match tokens on (linguistic) attributes and annotations are added to
    matching sequences.
    
    See the following spaCy documentation for further implementation details:
    - rule-based matching: https://spacy.io/usage/rule-based-matching
    - custom extension attributes: https://spacy.io/usage/processing-pipelines#custom-components-attributes
    
    # TODO remove use of hard-coded conditional imports to load rule files.
    # Replace this with a grammar rule parser (e.g. PLY).
"""

import spacy
import sys

from spacy.matcher import Matcher
from spacy.tokens import Span

# Ad hoc import selection

# This is an ad hoc workaround to avoid trying to overwrite default attributes
# TODO Find a better, cleaner solution as this will not apply to version changes
DEFAULT_ATTRIBUTES = ['DEP', 'HEAD', 'IS_ALPHA', 'IS_ASCII', 'IS_BRACKET', 
                      'IS_CURRENCY', 'IS_DIGIT', 'IS_LEFT_PUNCT', 'IS_LOWER',
                      'IS_OOV', 'IS_PUNCT', 'IS_QUOTE', 'IS_RIGHT_PUNCT',
                      'IS_SPACE', 'IS_STOP', 'IS_TITLE', 'IS_UPPER', 'LEMMA',
                      'LENGTH', 'LIKE_EMAIL', 'LIKE_NUM', 'LIKE_URL', 'LOWER',
                      'ORTH', 'POS', 'PREFIX', 'SENT_START', 'SHAPE', 'SUFFIX',
                      'TAG']


class TokenSequenceAnnotator(object):
    """
    Token Sequence Annotator
    
    Initialises a single new spaCy pipeline component that annotates tokens 
    according to a set of grammar rules specified in an external file.
    """
    
    def __init__(self, nlp, name, verbose=True):
        """
        Create a new TokenSequenceAnnotator instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
            - name: str; the name suffix of the component.
            - verbose: bool; print all messages
        """
        self.name = 'token_sequence_annotator_' + name
        # using conditional import while waiting to implement a grammar parser
        self.rules = []
        if name == 'test':
            from resources.token_sequence_rules_test import TEST_RULES
            self.rules = TEST_RULES
        elif name == 'level0':
            from resources.token_sequence_rules import RULES
            self.rules = RULES
        elif name == 'level0_fem':
            from resources.token_sequence_rules_fem import RULES
            self.rules = RULES
        elif name == 'level1':
            from resources.token_sequence_rules_1 import RULES_1
            self.rules = RULES_1
        elif name == 'level1_fem':
            from resources.token_sequence_rules_1_fem import RULES_1
            self.rules = RULES_1
        elif name == 'time':
            from resources.token_sequence_rules_time import RULES_TIME
            self.rules = RULES_TIME
        elif name == 'time_fem':
            from resources.token_sequence_rules_time_fem import RULES_TIME
            self.rules = RULES_TIME
        elif name == 'negation':
            from resources.token_sequence_rules_negation import RULES_NEGATION
            self.rules = RULES_NEGATION
        elif name == 'status':
            from resources.token_sequence_rules_status import RULES_STATUS
            self.rules = RULES_STATUS
        elif name == 'status_fem':
            from resources.token_sequence_rules_status_fem import RULES_STATUS
            self.rules = RULES_STATUS
        elif name == 'history':
            from resources.token_sequence_rules_history import RULES_HISTORY
            self.rules = RULES_HISTORY
        self.nlp = nlp
        self.matcher = None
        self.matches = {}
        self.verbose = verbose

    def __call__(self, doc):
        if self.verbose:
            print('-- Token sequence annotator:', self.name)
        
        # clear matches - this is required as we initialise this component only
        # once and matches from previous documents need to be erased
        self.matches = {}
        
        for rule in self.rules:
            pattern = rule['pattern']
            name = rule['name']
            avm = rule['avm']
            merge = rule.get('merge', False)
            # TODO add possibility of setting new attributes for merged spans in the rules
            # attrs = rule.get('attrs', [])

            self.matcher = Matcher(self.nlp.vocab)  # Need to do this for each rule separately unfortunately
            self.matcher.add(name, None, pattern)

            matches = self.matcher(doc)

            # store all matched spans for subsequent merging
            spans = {}
            for match in matches:
                start = match[1]
                end = match[2]
                span = Span(doc, start, end)  # store offsets for longest match selection
                spans[(start, end)] = span

            if len(spans) > 0:
                self.matches[rule['name']] = [matches, spans, merge]
            self.add_annotation(doc, matches, name, avm)

            if self.verbose:
                print('  -- Rule ' + name + ': ' + str(len(matches)) + ' matches.', file=sys.stderr)

        # retain only longest matching spans
        """
        self.get_longest_matches()

        # perform merging where specified by the rule
        for rule_name in self.matches:
            rule_matches = self.matches[rule_name]
            spans = rule_matches[1]
            merge = rule_matches[2]
            if merge:
                with doc.retokenize() as retokenizer:
                    for offsets in spans:
                        span = spans[offsets]
                        try:
                            if self.verbose:
                                print('  -- Merging span from rule ' + rule_name + ':', [token for token in span], file=sys.stderr)
                            retokenizer.merge(span)
                            #span.merge() # old API, more error-prone apparently
                        except IndexError as e:
                            print('  -- Warning: unable to merge span at', offsets, '(token may have been merged previously).', file=sys.stderr)
                            print(e, file=sys.stderr)
        """

        return doc
    
    def load_rules(self):
        # TODO write grammar parser
        pass

    def get_longest_matches(self):
        """
        Remove all shortest matching overlapping spans.
        """

        def get_overlapping_spans(spans):
            """ Get a unique list of all overlapping span offsets """
            offsets = spans.keys()
            overlaps = {}
            for offset in offsets:
                o = [(i[0], i[1]) for i in offsets if
                     i[0] >= offset[0] and i[0] <= offset[1] or i[1] >= offset[0] and i[1] <= offset[1] if
                     (i[0], i[1]) != offset and (i[0], i[1]) and (i[0], i[1]) not in overlaps]
                if len(o) > 0:
                    overlaps[offset] = o

            return [[k] + v for (k, v) in overlaps.items()]

        rule_names = self.matches.keys()
        for rule_name in rule_names:
            match = self.matches[rule_name]
            all_spans = match[1]
            overlapping_spans = get_overlapping_spans(all_spans)
            for os in overlapping_spans:
                shortest_spans = sorted(os, key=lambda x: x[1] - x[0], reverse=True)[1:]
                # pop shortest spans
                for ss in shortest_spans:
                    # avoid trying to remove a span more than once
                    if ss in all_spans:
                        all_spans.pop(ss)

    def add_annotation(self, doc, matches, rule_name, rule_avm):
        """
        Add annotations to the specified tokens in a match.
        NOTE: does not work with operators.
        
        Arguments:
            - doc: spaCy Doc; the current spaCy document object.
            - matches: list; the matched token sequences
            - rule_avm: dict; the attribute-value pair dictionary specified in
                        the annotation rule
            - merge: bool; merge matched spans
        """
        # TODO this is really ugly, tidy it up
        for match in matches:
            start = match[1]
            end = match[2]
            span = doc[start:end] # why was this end + 1?
            if self.verbose:
                print('  -- Match:', rule_name, match, doc[start:end], file=sys.stderr)
            # First check if rule annotates ALL tokens (this is to deal with multi-token operators (+, *)
            new_annotations = rule_avm.get('ALL', None)
            if new_annotations is not None:
                for new_attr in new_annotations:
                    for j in range(len(span)):
                        token = span[j]
                        val = new_annotations[new_attr]
                        if new_attr in DEFAULT_ATTRIBUTES:
                            print('  -- Warning: cannot modify built-in attribute', new_attr, ' in rule', rule_name, file=sys.stderr)
                        else:
                            token._.set(new_attr, val)
            else:
                new_annotations = rule_avm.get('LAST', None)

                if new_annotations is not None:
                    for new_attr in new_annotations:
                        token = span[len(span) - 1]
                        val = new_annotations[new_attr]
                        if new_attr in DEFAULT_ATTRIBUTES:
                            print('  -- Warning: cannot modify built-in attribute', new_attr, ' in rule', rule_name,  file=sys.stderr)
                        else:
                            token._.set(new_attr, val)

                # Now annotate token-by-token according to rule (for rules with LAST and integers)
                int_keys = [key for key in rule_avm.keys() if isinstance(key, int)]
                for key in int_keys:
                    new_annotations = rule_avm.get(key, None)
                    for j in range(len(span)):
                        if j in rule_avm.keys():
                            new_annotations = rule_avm.get(j, None)
                            if new_annotations is not None:
                                for new_attr in new_annotations:
                                    token = span[j]
                                    val = new_annotations[new_attr]
                                    if new_attr in DEFAULT_ATTRIBUTES:
                                        print('  -- Warning: cannot modify built-in attribute', new_attr, ' in rule', rule_name,  file=sys.stderr)
                                    else:
                                        token._.set(new_attr, val)

    def print_spans(self, doc):
        """
        Output all spans in CoNLL-style token annotations to stdout

        Arguments:
            - doc: spaCy Doc; the current Doc object
        """
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
    nlp = spacy.load('en_core_web_sm')

    text = 'No signs of self-harm reported by patient, but her mother cut her arm and \
    cut her legs. I will be very very very happy. I have apples and bananas.'

    tsa = TokenSequenceAnnotator(nlp, 'test')
    nlp.add_pipe(tsa)
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names, file=sys.stderr)
    tsa.print_spans(doc)
