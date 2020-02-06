# -*- coding: utf-8 -*-

"""
    Delibrate Self-Harm (DSH) annotator

    This annotator marks up mentions of deliberate self-harm (DSH) in clinical
    texts. The algorithm determines whether a mention is negated or not,
    whether it is current or historical and whether it is relevant or not, as 
    defined by the parameters of the study.
    Output is in the XML stand-off annotation format that is used
    by the eHOST annotation tool (see https://code.google.com/archive/p/ehost/).

    Tag: Self-harm
    Attributes and values:
        polarity - NEGATIVE or POSITIVE
        status  - RELEVANT or NON-RELEVANT
        temporality - CURRENT or HISTORICAL

"""

import argparse
import os
import re
import spacy
import sys
import xml.etree.ElementTree as ET

from datetime import datetime
from lexical_annotator import LexicalAnnotatorSequence
from lexical_annotator import LemmaAnnotatorSequence
from token_sequence_annotator import TokenSequenceAnnotator
from detokenizer import Detokenizer
from spacy.symbols import LEMMA, LOWER
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

# store examples outside of main code
from examples.test_examples import text

__author__ = "André Bittar"
__copyright__ = "Copyright 2020, André Bittar"
__credits__ = ["André Bittar"]
__license__ = "GPL"
__email__ = "andre.bittar@kcl.ac.uk"

FWD_OFFSET = 10
BWD_OFFSET = 10


class DSHAnnotator:
    """
    Deliberate Self-Harm (DSH) annotator
    
    Annotate mentions of deliberate self-harm (DSH) in clinical texts.
    """

    def __init__(self, verbose=False):
        """
        Create a new DSHAnnotator instance.
        
        Arguments:
            - verbose: bool; print all messages.
        """
        print('DSH annotator')
        self.nlp = spacy.load('en_core_web_sm', disable=['ner'])
        self.text = None
        self.verbose = verbose
        
        # initialise
        # Load pronoun lemma corrector
        self.load_pronoun_lemma_corrector()
        
        # Load date annotator
        self.load_date_annotator()

        # Load detokenizer
        self.load_detokenizer(os.path.join('resources', 'detokenization_rules.txt'))

        # Load lexical annotators
        self.load_lexicon('./resources/history_type_lex.txt', LOWER, 'LA')
        self.load_lexicon('./resources/dsh_lex.txt', LEMMA, 'DSH')
        #self.load_lexicon('./resources/time_past_lex.txt', LEMMA, 'TIME')
        self.load_lexicon('./resources/time_past_lex.txt', LOWER, 'TIME')
        self.load_lexicon('./resources/time_present_lex.txt', LEMMA, 'TIME')
        self.load_lexicon('./resources/time_life_stage_lex.txt', LEMMA, 'TIME')
        self.load_lexicon('./resources/negation_lex.txt', LEMMA, 'NEG')
        self.load_lexicon('./resources/modality_lex.txt', LEMMA, 'MODALITY')
        self.load_lexicon('./resources/hedging_lex.txt', LEMMA, 'HEDGING')
        self.load_lexicon('./resources/intent_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/body_part_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/harm_action_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/med_lex.txt', LEMMA, 'LA')
        #self.load_lexicon('./resources/reported_speech_lex.txt', LEMMA, 'RSPEECH')

        # Load token sequence annotators
        self.load_token_sequence_annotator('history')
        self.load_token_sequence_annotator('level0')
        self.load_token_sequence_annotator('level1')
        self.load_token_sequence_annotator('time')
        self.load_token_sequence_annotator('negation')
        self.load_token_sequence_annotator('status')
        
        print('-- Pipeline:', file=sys.stderr)
        print('  -- ' + '\n  -- '.join(self.nlp.pipe_names), file=sys.stderr)

    def load_lexicon(self, path, source_attribute, target_attribute, merge=False):
        """
        Load a lexicon/terminology file for annotation.
        
        Arguments:
            - path: str; the path to the lexicon file.
            - source_attribute: spaCy symbol; the token attribute to match
              on (e.g. LEMMA).
            - target_attribute: spaCy symbol; the token attribute to add the 
              lexical annotations to (e.g. TAG, or custom attribute LA, DSH).
            - merge: bool; merge annotated spans into a single span.
        """
        print(path, source_attribute, target_attribute, merge)
        if source_attribute == LEMMA:
            lsa = LemmaAnnotatorSequence(self.nlp, path, target_attribute, merge=merge)
        else:
            lsa = LexicalAnnotatorSequence(self.nlp, path, source_attribute, target_attribute, merge=merge)
        lsa.load_lexicon()
        self.nlp = lsa.add_components()

    def load_pronoun_lemma_corrector(self):
        """
        Load a pipeline component to convert spaCy pronoun lemma (-PRON-) into
        the corresponding word form,
        e.g. ORTH=her LEMMA=-PRON- -> ORTH=her, LEMMA=her.
        """
        component = LemmaCorrector()
        pipe_name = component.name

        if not pipe_name in self.nlp.pipe_names:
            self.nlp.add_pipe(component, last=True)
        else:
            print('-- ', pipe_name, 'exists already. Component not added.')

    def load_date_annotator(self):
        """
        Load a pipeline component to match and annotate certain date 
        expressions.
        """
        component = DateTokenAnnotator()
        pipe_name = component.name

        if not pipe_name in self.nlp.pipe_names:
            self.nlp.add_pipe(component, last=True)
        else:
            print('-- ', pipe_name, 'exists already. Component not added.')

    def load_detokenizer(self, path):
        """
        Load a pipeline component that stores detokenization rules loaded from 
        a file.
        
        Arguments:
            - path: str; the path to the file containing detokenization rules.
        """
        print('-- Detokenizer')
        self.nlp = Detokenizer(self.nlp).load_detokenization_rules(path, verbose=self.verbose)

    def load_token_sequence_annotator(self, name):
        """
        Load a token sequence annotator pipeline component.
        TODO allow for multiple annotators, cf. lemma and lexical annotators.
        TODO add path argument to specify rule file.
        
        Arguments:
            - name: str; the name of the token sequence annotator - this 
                    *must* be the name (without the .py extension) of the file
                    containing the token sequence rules.
        """
        tsa = TokenSequenceAnnotator(self.nlp, name, verbose=self.verbose)
        if tsa.name not in self.nlp.pipe_names:
            self.nlp.add_pipe(tsa)

    def get_text(self):
        """
        Return the text of the current annotator instance.
        
        Return:
            - text: str; the text of the document being processed.
        """
        return self.text

    def normalise(self, text):
        """
        Normalise the text.
        # TODO: Add normalisation rules if we want to clean things up first.
        
        Arguments:
            - text: str; the text to be normalised.
        
        Return:
            - text: str; the normalised text.
        """
        text = re.sub(' +', ' ', text)
        return text

    def annotate_text(self, text):
        """
        Annotate a text string.
        
        Arguments:
            - text: str; the text to annotate.
        
        Return:
            - doc: spaCy Doc; the annotated Doc object.
        """
        self.text = text
        doc = self.nlp(text)
        return doc

    def annotate_file(self, path):
        """
        Annotate the contents of a text file.
        
        Arguments:
            - path: str; the path to a text file to annotate.
        
        Return:
            - doc: spacy Doc; the annotated Doc object.
        """
        # TODO check for file in input
        # TODO check encoding
        f = open(path, 'r', encoding='Latin-1')
        self.text = f.read()

        if len(self.text) >= 1000000:
            print('-- Unable to process very long text text:', path)
            return None

        doc = self.nlp(self.text)
        
        return doc

    def has_negation_ancestor(self, curr_token, verbose=False):
        """
        Search the dependency tree for a negation marker.
        
        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
            - verbose: bool; print all messages.
        
        Return: bool; True if negation found, else False.
        """
        if verbose:
            print('-- Detecting negations...', curr_token)

        if curr_token.lemma_ in ['report', 'say', 'claim', 'announce', 'insist']:
            for child in curr_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', curr_token)
                if child.dep_ == 'neg':
                    return True
            #return False

        elif curr_token.lemma_ in ['deny']:
            return True

        elif curr_token.pos_.startswith('N'):
            for child in curr_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', curr_token)
                if child.dep_ == 'neg' or child.lemma_ in ['no']:
                    return True
            #return False

        elif curr_token.pos_.startswith('V'):
            for child in curr_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', curr_token)
                if child.dep_ == 'neg':
                    return True
            #return False

        if curr_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.has_negation_ancestor(curr_token.head, verbose=verbose)

    def has_historical_ancestor(self, curr_token, verbose=False):
        """
        Search the dependency tree for an ancestor of the current node that is
        a marker of historical temporality.
        
        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
            - verbose: bool; print all messages.
        
        Return: bool; True if historical marker found, else False.
        """
        if verbose:
            print('-- Detecting historical ancestors...', curr_token)
        
        if curr_token._.TIME == 'TIME':
            return True

        if curr_token.dep_ == 'ROOT':
            return False

        return self.has_historical_ancestor(curr_token.head, verbose=verbose)

    def has_historical_dependent(self, curr_token, verbose=False):
        """
        Search the dependency tree for an dependent of the current node that is
        a marker of historical temporality.

        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
            - verbose: bool; print all messages.
        
        Return: bool; True if historical marker found, else False.
        """
        if verbose:
            print('-- Detecting historical modifiers...', curr_token)

        if curr_token.tag_ in ['VBG', 'VBN']:
            for child in curr_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', curr_token)
                if child.lower_ == 'had':
                    return True
                self.has_historical_dependent(child, verbose=verbose)

        if curr_token.pos_[0] in ['N', 'V']:
            for child in curr_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', curr_token)
                if child._.TIME == 'TIME':
                    return True
                self.has_historical_dependent(child, verbose=verbose)

        return False

    def has_hedging_ancestor(self, curr_token, verbose=True):
        """
        Search the dependency tree for an ancestor of the current node that is
        a marker of hedging.
        
        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
            - verbose: bool; print all messages.
        
        Return: bool; True if hedging marker found, else False.
        """
        if curr_token._.HEDGING == 'HEDGING':
            return True
        
        if curr_token.dep_ == 'ROOT':
            # ROOT
            return False
        
        return self.has_hedging_ancestor(curr_token.head, verbose=verbose)
    
    def has_hedging_dependent(self, curr_token, verbose=True):
        """
        Search the dependency tree for an dependent of the current node that is
        a marker of hedging.

        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
            - verbose: bool; print all messages.
        
        Return: bool; True if hedging marker found, else False.
        """
        for child in curr_token.children:
            if child._.HEDGING == 'HEDGING':
                return True
            self.has_hedging_dependent(child, verbose=verbose)
        
        return False

    def has_hedging_noun_previous(self, doc, i, verbose=False):
        """
        Search for a hedging noun in the preceding tokens within the current
        sentence.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - i: int; the token index in the current Doc object to 
                 search from.
        
        Return: bool; True if hedging noun found, else False.
        """
        start = doc[i].sent.start
        end = doc[i].i
        if verbose:
            print('-- Checking for previous hedging noun...')
        for j in range(end, start, -1):
            token = doc[j]
            # A colon indicates previous words are likely to be a list heading,
            # and so are irrelevant
            if token.lemma_ == ':':
                return False
            if token.pos_[0] == 'N' and not token._.DSH:
                if token._.HEDGING == 'HEDGING':
                    return True
            # Deal with merged spans that may not have the correct POS, e.g. suicidal thoughts
            if re.search('idea(tion)?|intent|thought', token.head.lemma_, flags=re.I) is not None:
                return True

        return False
    
    def has_past_tense_governor(self, curr_token):
        """
        Check if the current token's governor is a past tense verb.
        WARNING: This had a disastrous effect on results; not in use.
        
        Arguments:
            - curr_token: spacy Token; the current token.
        
        Return: bool; True if past tense governor found, else False.
        """
        return curr_token.head.tag_ in ['VBD', 'VBN', 'VHD', 'VHN', 'VVD', 'VVN']
    
    def has_propatt_ancestor(self, curr_token):
        """
        Search the dependency tree for a propositional attitude ancestor of the
        current token.
        
        Arguments:
            - curr_token: spaCy Token; the token to start searching from.
        
        Return: bool; True if propositional attitude marker found, else False.
        """
        if curr_token.head.pos_ == 'VERB':
            if curr_token.head.lemma_ in ['believe', 'desire', 'dream', 'feel', 'imagine', 'think', 'want', 'wish', 'wonder']:
                return True

        if curr_token.head.pos_ == 'NOUN':
            if curr_token.head.lemma_ in ['assumption', 'belief', 'feeling', 'desire', 'dream', 'idea', 'opinion', 'wish', 'view']:
                return True

        if curr_token.head._.DSH == 'NON_DSH':
            # e.g. suicidal thoughts   
            match = re.search('idea(tion)?|intent|thought', curr_token.head.lemma_, flags=re.I)
            return match is not None

        if curr_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.has_propatt_ancestor(curr_token.head)
    
    def is_reported_speech(self, curr_token):
        """
        Check if the current token's governor is a reported speech verb.
        NOTE: not in use.
        
        Arguments:
            - curr_token: spacy Token; the current token.
        
        Return: bool; True if reported speech verb found, else False.
        """
        if curr_token.head._.RSPEECH == 'TRUE':
            return True

        if curr_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.is_reported_speech(curr_token.head.head)
    
    def is_section_header(self, doc, i, verbose=True):
        """
        Check if a given position in the document is part of a section header.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - i: int; the token index in the current Doc object to search from.

        Return: bool; True if section header, else False.
        """
        cur_sent = doc[i].sent
        end = len(cur_sent) - 1
        window = cur_sent[i:end].text
        if re.search(':', window) is not None:
            return True
        return False
    
    def is_singleton(self, doc, i):
        """
        Check if the token at a specified index is the only one in the sentence.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - i: int; the token index in the current Doc object to check.
        
        Return: bool; True if section header, else False.
        """
        if doc[i].text == doc[i].sent.text:
            return True
        return False
    
    def is_definite(self, doc, i):
        """
        Check if the token at a specified position governs a definite or 
        possessive determiner.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - i: int; the token index in the current Doc object to check.
        
        Return: bool; True if definite or possessive determiner found, else False.
        """
        for child in doc[i].children:
            if child.lemma_ in ['the', 'this', 'that', 'her']:
                return True
        return False
    
    def calculate_dsh_mention_attributes(self, doc, verbose=False):
        """
        Using previously added annotations, calculate the attribute values for 
        all detected mentions, and determine whether the document has a history
        section.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - verbose: bool; print all messages.
        
        Return:
            - has_history_section: bool; True if a history section was detected
                                   in the document, else False.
        
        """
        # Hack: get attributes from window of 5 tokens before DSH mention
        has_history_section = False
        for i in range(len(doc)):
            if doc[i]._.DSH in ['DSH', 'NON_DSH']:

                # if token is in a history section annotate as historical
                if doc[i]._.HISTORY == 'HISTORY':
                    has_history_section = True
                    doc[i]._.TIME = 'TIME'
                    print('#####', doc[i])

                if self.has_negation_ancestor(doc[i]) and not self.is_definite(doc, i):
                    if verbose:
                        print('-- Negation detected for', doc[i])
                    doc[i]._.NEG = 'NEG'
                
                if self.has_hedging_noun_previous(doc, i):
                    if verbose:
                        print('-- Hedging noun detected for', doc[i])
                    doc[i]._.HEDGING = 'HEDGING'
                
                if self.is_singleton(doc, i):
                    # mark as HEDGING (NON-RELEVANT)
                    if verbose:
                        print('-- Singleton', doc[i])
                    doc[i]._.HEDGING = 'HEDGING'
                
                if self.is_section_header(doc, i):
                    if verbose:
                        print('-- Section header', doc[i])
                    doc[i]._.HEDGING = 'HEDGING'
                
                # Lowers results
                #if self.has_propatt_ancestor(doc[i]):
                #    print('-- Propositional attitude', doc[i])
                #    doc[i]._.HEDGING = 'HEDGING'
                
                # Lowers results
                #if self.has_hedging_ancestor(doc[i]):
                #    print('-- Hedging ancestor detected for', doc[i])
                #    doc[i]._.HEDGING = 'HEDGING'

                # Lowers results
                #if self.has_hedging_dependent(doc[i]):
                #    print('-- Hedging dependent detected for', doc[i])
                #    doc[i]._.HEDGING = 'HEDGING'
                
                # Slight decrease p, slight increase r, slight increase f
                #if self.has_historical_ancestor(doc[i]):
                #    print('-- Historical marker detected for', doc[i])
                #    doc[i]._.TIME = 'TIME'

                # Lowers results
                #if self.has_historical_dependent(doc[i]):
                #    print('-- Historical marker detected for', doc[i])
                #    doc[i]._.TIME = 'TIME'

                # Check previous tokens in window going back from mention
                curr_sent = doc[i].sent
                start = i - BWD_OFFSET
                if start < 0:
                    start = curr_sent.start
                window = doc[start:i]
                for token in reversed(window):
                    if token.sent == curr_sent:
                        # Intended to deal with incorrect HEDGING, but reduces
                        # performance on other attributes for a slight improvement
                        # A colon indicates previous words are likely to be a list heading,
                        # and so are irrelevant
                        #if token.lemma_ == ':':
                        #    break
                        # Improves status, decreases temporality
                        # Break on newline, consider it a sentence boundary
                        #if token.pos_ == 'SPACE':
                        #    break
                        # Definite mentions are positive
                        found_present = False
                        if not self.is_definite(doc, i) and token._.NEG == 'NEG':
                            doc[i]._.NEG = 'NEG'
                        if not found_present and token._.TIME in ['TIME', 'PAST']:
                            doc[i]._.TIME = 'TIME'
                        # Overwrite past mentions with present
                        if token._.TIME == 'PRESENT':
                            doc[i]._.TIME = False
                            found_present = True
                        if token._.MODALITY == 'MODALITY':
                            doc[i]._.MODALITY = 'MODALITY'
                        if token._.HEDGING == 'HEDGING':
                            doc[i]._.HEDGING = 'HEDGING'

        # Hack: get attributes from window of 5 tokens after DSH mention in the same sentence
        for i in range(len(doc)):
            if doc[i]._.DSH in ['DSH', 'NON_DSH']:
                curr_sent = doc[i].sent
                end = i + FWD_OFFSET
                if end > curr_sent.start + len(curr_sent):
                    end = curr_sent.start + len(curr_sent)
                window = doc[i:end]
                found_CCONJ = False # used for MODALITY and HEDGING
                for token in window:
                    if token.sent == curr_sent:
                        # Increases status for MODALITY and HEDGING, not TIME
                        # Coordinating conjunction is a syntactic "barrier", 
                        # so we avoid examining features beyond.
                        if token.pos_ == 'CCONJ':
                            if verbose:
                                print('-- Found subsequent CCONJ', token.text)
                            found_CCONJ = True
                        if token._.TIME in ['TIME', 'PAST']:
                            doc[i]._.TIME = 'TIME'
                        if token._.MODALITY == 'MODALITY':
                            if not found_CCONJ:
                                doc[i]._.MODALITY = 'MODALITY'
                        if token._.HEDGING == 'HEDGING':
                            if not found_CCONJ:
                                doc[i]._.HEDGING = 'HEDGING'

        return has_history_section

    def merge_spans(self, doc):
        """
        Merge all longest matching DSH token sequences into single spans.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
        
        Return:
            - doc: spaCy Doc; the current Doc object with merged longest spans.
        """

        def get_longest_spans(offsets):
            """
            Get a unique list of all overlapping span offsets.
            
            Arguments:
                - offsets: list; the list of offsets.
            
            Return:
                - offsets: list; the list of offsets sorted in decreasing order
                           of difference between start and end.
            """
            overlaps = {}
            for offset in offsets:
                o = [(i[0], i[1]) for i in offsets if
                     i[0] >= offset[0] and i[0] <= offset[1] or i[1] >= offset[0] and i[1] <= offset[1] if
                     (i[0], i[1]) != offset and (i[0], i[1]) and (i[0], i[1]) not in overlaps]
                if len(o) > 0:
                    overlaps[offset] = o

            for offset in [[k] + v for (k, v) in overlaps.items()]:
                shortest_spans = sorted(offset, key=lambda x: x[1] - x[0], reverse=True)[1:]
                for ss in shortest_spans:
                    if ss in offsets:
                        offsets.remove(ss)
            
            return offsets

        offsets = []
        i = 0
        while i < len(doc):
            token = doc[i]
            if token._.DSH:
                start = i
                while token._.DSH:
                    i += 1
                    if i == len(doc):
                        print('-- Warning: index is equal to document length:', i, token, len(doc), file=sys.stderr)
                        break
                    token = doc[i]
                end = i
                offsets.append((start, end))
            i += 1

        #print('BEFORE:', offsets, file=sys.stderr)
        #offsets = get_longest_spans(offsets)
        #print('AFTER :', offsets, file=sys.stderr)
        
        with doc.retokenize() as retokenizer:
            for (start, end) in offsets:
                #print('Merging tokens:', start, end, doc[start:end], file=sys.stderr)
                attrs = {'LEMMA': ' '.join([token.lemma_ for token in doc[start:end]])}
                retokenizer.merge(doc[start:end], attrs=attrs)

        return doc
        
    def print_tokens(self, doc, path):
        """
        Output all tokens in CoNLL-style token annotations to stdout and write 
        to file.
        
        Arguments:
            - doc: spaCy Doc; the current Doc object.
            - path: str; the file path to write output to (will overwrite 
                    any existing file).
        """
        with open(path, 'w') as fout:
            for token in doc:
                string = '{:<10}{:<15}{:<15}{:<15}{:<15}{:<15}{:<15}'.format(token.i, token.text, token.lemma_, token.tag_, dsha.nlp.vocab.strings[token._.dsh] or '_', dsha.nlp.vocab.strings[token._.sem] or '_', token.head.i, token.dep_)
                print(string, file=fout)
                print(string)
        fout.close()

    def print_spans(self, doc):
        """
        Output all spans in CoNLL-style token annotations to stdout

        Arguments:
            - doc: spaCy Doc; the current Doc object
        """
        s = '\n'
        s += 'PIPELINE:\n-- ' + '\n-- '.join(self.nlp.pipe_names)
        s += '\n\n'
        s += '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format('INDEX', 'WORD', 'LEMMA', 'LOWER', 'POS1', 'POS2', 'HEAD', 'DEP')

        cext = set()        
        for a in doc.user_data:
            cext.add(a[1])

        cext = sorted(cext)

        for a in cext:
            s += '{:<10}'.format(a)

        s += '\n'

        s += '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format('-----', '----', '-----', '----', '----', '----', '----', '----')

        for a in cext:
            s += '{:<10}'.format('-' * len(a))

        print(s, file=sys.stderr)
        
        for token in doc:
            s = '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format(token.i, token.text, token.lemma_, token.lower_, token.tag_, token.pos_, token.head.i, token.dep_)
            for a in cext:
                val = token._.get(a)
                s += '{:10}'.format(val or '_')
            print(s, file=sys.stderr)

    def build_ehost_output(self, doc):
        """
        Construct a dictionary representation of all annotations.

        Arguments:
            - doc: spacy Doc; the processed spaCy Doc object.
        
        Return:
            - mentions: dict; a dictionary containing all annotations ready for
                        output in eHOST XML format.
        """
        mentions = {}
        n = 1
        for token in doc:
            if token._.DSH == 'DSH':
                mention_id = 'EHOST_Instance_' + str(n)
                annotator = 'SYSTEM'
                mclass = 'SELF-HARM'
                comment = None
                start = token.idx
                end = token.idx + len(token.text)
                polarity = 'POSITIVE'
                status = 'RELEVANT'
                temporality = 'CURRENT'
                text = token.text
                if token._.NEG == 'NEG':
                    polarity = 'NEGATIVE'
                    status = 'NON-RELEVANT'
                if token._.MODALITY == 'MODALITY':
                    status = 'UNCERTAIN'
                if token._.HEDGING == 'HEDGING':
                    status = 'NON-RELEVANT'
                if token._.HEDGING == 'UNCERTAIN':
                    status = 'UNCERTAIN'
                if token._.TIME in ['HISTORICAL', 'TIME']:
                    temporality = 'HISTORICAL'
                n += 1
                mentions[mention_id] = {'annotator': annotator,
                                        'class': mclass,
                                        'comment': comment,
                                        'end': str(end),
                                        'polarity': polarity,
                                        'start': str(start),
                                        'status': status,
                                        'temporality': temporality,
                                        'text': text
                                        }
            elif token._.DSH == 'NON_DSH':
                mention_id = 'EHOST_Instance_' + str(n)
                annotator = 'SYSTEM'
                mclass = 'SELF-HARM'
                comment = None
                start = token.idx
                end = token.idx + len(token.text)
                polarity = 'POSITIVE'
                status = 'NON-RELEVANT'
                temporality = 'CURRENT'
                text = token.text
                if token._.NEG == 'NEG':
                    polarity = 'NEGATIVE'
                if token._.TIME in ['HISTORICAL', 'TIME']:
                    temporality = 'HISTORICAL'
                n += 1
                mentions[mention_id] = {'annotator': annotator,
                                        'class': mclass,
                                        'comment': comment,
                                        'end': str(end),
                                        'polarity': polarity,
                                        'start': str(start),
                                        'status': status,
                                        'temporality': temporality,
                                        'text': text
                                        }
        
        return mentions

    def write_ehost_output(self, pin, annotations, verbose=False):
        """
        Write an annotated eHOST XML file to disk.
        
        Arguments:
            - pin: str; the input file path (must be in eHOST directory structure).
            - annotations: dict; the dictionary of detected annotations.
            - verbose: bool; print all messages.
        
        Return:
            - root: Element; the root node of the new XML ElementTree object.
        """
        ehost_pout = os.path.splitext(pin.replace('corpus', 'saved'))[0] + '.txt.knowtator.xml'

        root = ET.Element('annotations')
        root.attrib['textSource'] = os.path.basename(os.path.splitext(pin.replace('.knowtator.xml', ''))[0] + '.txt')

        n = 1
        m = 1000
        for annotation_id in sorted(annotations.keys()):
            annotation = annotations[annotation_id]

            annotation_node = ET.SubElement(root, 'annotation')
            mention = ET.SubElement(annotation_node, 'mention')
            mention_id = 'EHOST_Instance_' + str(n)
            mention.attrib['id'] = mention_id
            annotator = ET.SubElement(annotation_node, 'annotator')
            annotator.attrib['id'] = 'eHOST_2010'
            annotator.text = annotation['annotator']
            spanned_text = ET.SubElement(annotation_node, 'spannedText')

            if annotation.get('comment', None) is not None:
                comment = ET.SubElement(annotation_node, 'annotationComment')
                comment.text = annotation['comment']

            creation_date = ET.SubElement(annotation_node, 'creationDate')
            creation_date.text = datetime.now().strftime('%a %b %d %H:%M:%S %Z%Y')

            span = ET.SubElement(annotation_node, 'span')
            span.attrib['start'] = annotation['start']
            span.attrib['end'] = annotation['end']

            spanned_text.text = annotation['text']

            class_mention = ET.SubElement(root, 'classMention')
            class_mention.attrib['id'] = mention_id
            mention_class_node = ET.SubElement(class_mention, 'mentionClass')
            mention_class_node.attrib['id'] = annotation['class']
            mention_class_node.text = annotation['text']

            # polarity
            val = annotation.get('polarity', 'POSITIVE')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'polarity'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)

            # status
            m += 1
            val = annotation.get('status', 'NON-RELEVANT')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'status'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)

            # temporality
            m += 1
            val = annotation.get('temporality', 'CURRENT')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'temporality'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(m)
            
            n += 1
            m += 1

        # Create Adjudication status with default values
        adj_status = ET.SubElement(root, 'eHOST_Adjudication_Status')
        adj_status.attrib['version'] = '1.0'
        adj_sa = ET.SubElement(adj_status, 'Adjudication_Selected_Annotators')
        adj_sa.attrib['version'] = '1.0'
        adj_sc = ET.SubElement(adj_status, 'Adjudication_Selected_Classes')
        adj_sc.attrib['version'] = '1.0'
        adj_o = ET.SubElement(adj_status, 'Adjudication_Others')
        check_s = ET.SubElement(adj_o, 'CHECK_OVERLAPPED_SPANS')
        check_s.text = 'false'
        check_a = ET.SubElement(adj_o, 'CHECK_ATTRIBUTES')
        check_a.text = 'false'
        check_r = ET.SubElement(adj_o, 'CHECK_RELATIONSHIP')
        check_r.text = 'false'
        check_cl = ET.SubElement(adj_o, 'CHECK_CLASS')
        check_cl.text = 'false'
        check_co = ET.SubElement(adj_o, 'CHECK_COMMENT')
        check_co.text = 'false'

        # Print to screen
        xmlstr = ET.tostring(root, encoding='utf8', method='xml')
        try:
            pxmlstr = parseString(xmlstr)
        except ExpatError as e:
            with open('./batch_err.log', 'a') as b_err:
                print('Unable to create XML file:', ehost_pout, file=b_err)
            b_err.close()
            return root

        if verbose:
            print(pxmlstr.toprettyxml(indent='\t'), file=sys.stderr)

        with open(ehost_pout, 'w') as fout:
            fout.write(pxmlstr.toprettyxml(indent='\t'))
        fout.close()

        if verbose:
            print('-- Wrote eHOST file: ' + ehost_pout, file=sys.stderr)

        return root

    def process(self, path, write_output=True):
        """
        Process a single document or directory structure.
        
        Arguments:
            - path: str; indicates text file or directory to process. If a directory, the
                structure must be that used by the eHOST annotation tool.
            - write_output: bool; save the annotated output to file.
        
        Return:
            - global_mentions: dict; a dictionary containing all annotated mentions.
        """
        global_mentions = {}

        if os.path.isdir(path):
            
            files = os.listdir(path)
            
            for f in files:
                pin = os.path.join(path, f)
                print('-- Processing file:', pin, file=sys.stderr)
                if self.verbose:
                    print('-- Processing file:', pin, file=sys.stderr)

                # Annotate and print results
                doc = self.annotate_file(pin)
                
                if doc is None:
                    return global_mentions
                
                self.calculate_dsh_mention_attributes(doc)
                
                doc = self.merge_spans(doc)
                
                if self.verbose:
                    self.print_spans(doc)
                
                mentions = self.build_ehost_output(doc)
                global_mentions[f + '.knowtator.xml'] = mentions
                
                if write_output:
                    self.write_ehost_output(pin, mentions, verbose=self.verbose)
                
        elif os.path.isfile(path):
            print('-- Processing file:', path, file=sys.stderr)
            doc = self.annotate_file(path)
            
            if doc is None:
                return global_mentions
            
            self.calculate_dsh_mention_attributes(doc)
            
            doc = self.merge_spans(doc)
            
            if self.verbose:
                self.print_spans(doc)
            
            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions

            if write_output:
                self.write_ehost_output(path, mentions, verbose=self.verbose)

        else:
            print('-- Processing text string:', path, file=sys.stderr)
            doc = self.nlp(path)
            self.calculate_dsh_mention_attributes(doc)

            doc = self.merge_spans(doc)

            if self.verbose:
                self.print_spans(doc)

            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions

            if write_output:
                self.write_ehost_output('test.txt', mentions, verbose=self.verbose)
        
        return global_mentions

    def process_text(self, text, text_id, write_output=False, verbose=False):
        """
        Process a text string.
        
        Arguments:
            - text: str; the input text.
            - text_id: str; a user-defined identifier for the text.
            - write_output: bool; write output to file.
            - verbose: bool; print all messages.

        Return:
            - global_mentions: dict; a dictionary containing all annotated mentions.
        """
        self.verbose = verbose
        if self.verbose:
            print('-- Processing text string:', text, file=sys.stderr)
        
        global_mentions = {}
        if text is None:
            print('-- Empty text:', text_id)
            return global_mentions
            
        if len(text) >= 1000000:
            print('-- Unable to process very long text text with id:', text_id)
            return global_mentions
        
        doc = self.nlp(text)
        flag = self.calculate_dsh_mention_attributes(doc)
        if flag:
            print('-- Found history section in text with id:', text_id)

        doc = self.merge_spans(doc)
        
        if self.verbose:
            self.print_spans(doc)

        mentions = self.build_ehost_output(doc)
        
        global_mentions[text_id] = mentions

        if write_output:
            self.write_ehost_output('output/test.txt', mentions, verbose=self.verbose)
        
        return global_mentions


class LemmaCorrector(object):
    """
    Lemma Corrector
    
    Replace spaCy's default lemma for relevant pronouns and other words.
    """

    def __init__(self):
        """
        Create a new LemmaCorrector instance.
        """
        self.name = 'pronoun_lemma_corrector'

    def __call__(self, doc):
        for token in doc:
            # relevant pronouns for peri-natal study
            if token.lower_ in ['she', 'her', 'herself', 'themselves']:
                token.lemma_ = token.lower_
            if token.lower_ == 'overdoses':
                token.lemma_ = 'overdose'
        return doc


class DateTokenAnnotator(object):
    """
    Date Token Annotator
    
    Annotate specific and easily matched date patterns.
    """

    def __init__(self):
        """
        Create a new DateTokenAnnotator instance.
        """
        self.name = 'date_token_annotator'

    def __call__(self, doc):
        # Date pattern regexes
        yyyy = '(19[0-9][0-9]|20[0-9])'
        ddmmyy = '(0?[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/([0-9][0-9])'
        ddmmyyyy = '(0?[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/(19[0-9][0-9]|20[0-9])'
        ddmmyy_dot = '(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])\.([0-9][0-9])'
        ddmmyyyy_dot = '(0?[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[012])\.(19[0-9][0-9]|20[0-9])'
        date = '(' + yyyy + '|' + ddmmyy + '|' + ddmmyyyy + '|' + ddmmyy_dot + '|' + ddmmyyyy_dot + ')'
        for token in doc:
            if re.search(date, token.lemma_) is not None:
                token._.TIME = 'TIME'
        return doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deliberate Self-Harm (DSH) Annotator')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-d', '--input_dir', type=str, nargs=1, help='the path to the directory containing text files to process.', required=False)
    group.add_argument('-f', '--input_file', type=str, nargs=1, help='the path to a text file to process.', required=False)
    group.add_argument('-t', '--text', type=str, nargs=1, help='a text string to process.', required=False)
    group.add_argument('-e', '--examples', action='store_true', help='run on test examples (no output to file).', required=False)
    parser.add_argument('-w', '--write_output', action='store_true', help='write output to file.', required=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode.', required=False)
    
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    
    dsha = DSHAnnotator(verbose=args.verbose)
    
    if args.text is not None:
        dsh_annotations = dsha.process_text(args.text[0], 'text_001', write_output=args.write_output, verbose=args.verbose)
    elif args.input_dir is not None:
        if os.path.isdir(args.input_dir[0]):
            dsh_annotations = dsha.process(args.input_dir[0], write_output=args.write_output)
        else:
            print('-- Error: argument -d/--input_dir must be an existing directory.\n')
            parser.print_help()
    elif args.input_file is not None:
        if os.path.isfile(args.input_file[0]):
            dsh_annotations = dsha.process(args.input_file[0], write_output=args.write_output)
        else:
            print('-- Error: argument -f/--input_file must be an existing text file.\n')
            parser.print_help()            
    elif args.examples:
        print('-- Running examples...', file=sys.stderr)
        dsh_annotations = dsha.process_text(text, 'text_001', write_output=False, verbose=True)
