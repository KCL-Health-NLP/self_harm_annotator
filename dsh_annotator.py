# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 14:27:31 2018

@author: ABittar
"""

import os
import spacy
import sys

from lexical_annotator import LexicalAnnotatorSequence
from lexical_annotator import LemmaAnnotatorSequence
from token_sequence_annotator import TokenSequenceAnnotator
from detokenizer import Detokenizer
from spacy.symbols import LEMMA


class DSHAnnotator:

    def __init__(self):
        self.nlp = spacy.load('en')
        self.text = None

    def load_lexicon(self, path, source_attribute, target_attribute, merge=False):
        """
        Load a lexicon/terminology file for annotation.
        """
        if source_attribute == LEMMA:
            lsa = LemmaAnnotatorSequence(self.nlp, path, target_attribute, merge=merge)
        else:
            lsa = LexicalAnnotatorSequence(self.nlp, path, target_attribute, merge=merge)
        lsa.load_lexicon()
        self.nlp = lsa.add_components()

    def load_pronoun_lemma_corrector(self):
        component = PronounLemmaCorrector()
        pipe_name = component.name

        if not pipe_name in self.nlp.pipe_names:
            self.nlp.add_pipe(component, last=True)
        else:
            print('-- ', pipe_name, 'exists already. Component not added.')

    def load_detokenizer(self, path):
        """
        Load all detokenization rules.
        """
        self.nlp = Detokenizer(self.nlp).load_detokenization_rules(path, verbose=True)

    def load_token_sequence_annotator(self, path):
        """
        Load all token sequence annotators.
        TODO allow for multiple annotators, cf. lemma and lexical annotators.
        TODO activate path argument.
        """
        tsa = TokenSequenceAnnotator(self.nlp)
        if tsa.name not in self.nlp.pipe_names:
            self.nlp.add_pipe(tsa)

    def get_text(self):
        return self.text

    def annotate_text(self, text):
        self.text = text
        return self.nlp(text)

    def annotate_file(self, path):
        # TODO check for file in input
        self.text = open(path, 'r').read()
        doc = self.nlp(self.text)
        
        return doc

    def calculate_dsh_mention_attributes(self, doc):
        # Hack: get attributes from window of 5 tokens before DSH mention
        for i in range(len(doc)):
            if doc[i]._.DSH == 'DSH':
                window = doc[i-5:i]
                for token in window:
                    if token._.NEG == 'NEG':
                        doc[i]._.NEG = 'NEG'
                    if token._.TIME == 'TIME':
                        doc[i]._.TIME = 'TIME'
                    if token._.MODALITY == 'MODALITY':
                        doc[i]._.MODALITY = 'MODALITY'

    def print_tokens(self, doc):
        with open('T:/Andre Bittar/workspace/ka_dsh/output/report.txt', 'w') as fout:
            for token in doc:
                string = '{:<10}{:<15}{:<15}{:<15}{:<15}{:<15}{:<15}'.format(token.i, token.text, token.lemma_, token.tag_, dsha.nlp.vocab.strings[token._.dsh] or '_', dsha.nlp.vocab.strings[token._.sem] or '_', token.head.i, token.dep_)
                print(string, file=fout)
                print(string)
        fout.close()

    def print_spans(self, doc):
        s = '\n'
        s += 'PIPELINE:\n-- ' + '\n-- '.join(self.nlp.pipe_names)
        s += '\n\n'
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

    def build_ehost_output(self, doc):
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
                    status = 'NON_RELEVANT'
                if token._.MODALITY == 'MODALITY':
                    status = 'NON_RELEVANT'
                if token._.TIME == 'TIME':
                    temporality = 'HISTORICAL'
                n += 1
                mentions[mention_id] = {'annotator': annotator,
                                        'class': mclass,
                                        'comment': comment,
                                        'end': end,
                                        'polarity': polarity,
                                        'start': start,
                                        'status': status,
                                        'temporality': temporality,
                                        'text': text
                                        }
        return mentions

    def process(self, path, verbose=False):
        # Load pronoun lemma corrector
        self.load_pronoun_lemma_corrector()

        # Load detokenizer
        self.load_detokenizer(os.path.join('resources', 'detokenization_rules.txt'))

        # Load lexical annotators
        self.load_lexicon('./resources/dsh_sequence_lex.txt', LEMMA, 'DSH', merge=True)
        self.load_lexicon('./resources/dsh_lex_lemma.txt', LEMMA, 'DSH', merge=True)
        self.load_lexicon('./resources/time_lex.txt', None, 'TIME')
        self.load_lexicon('./resources/negation_lex.txt', LEMMA, 'NEG')
        self.load_lexicon('./resources/modality_lex.txt', LEMMA, 'MODALITY')
        self.load_lexicon('./resources/body_part_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/harm_V_lex.txt', LEMMA, 'LA')

        # Load token sequence annotators
        dsha.load_token_sequence_annotator(None)

        global_mentions = {}

        if os.path.isdir(path):
            files = os.listdir(path)
            
            for f in files:
                pin = os.path.join(path, f)
                print('-- Processing file:', pin, file=sys.stderr)
                # Annotate and print results
                doc = self.annotate_file(pin)
                self.calculate_dsh_mention_attributes(doc)
                
                if verbose:
                    self.print_spans(doc)
                
                mentions = self.build_ehost_output(doc)
                global_mentions[f + '.knowtator.xml'] = mentions
                
        elif os.path.isfile(path):
            print('-- Processing file:', path, file=sys.stderr)
            doc = self.annotate_file(path)
            self.calculate_dsh_mention_attributes(doc)
            
            if verbose:
                self.print_spans(doc)
            
            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions
        else:
            print('-- Processing text string:', path, file=sys.stderr)
            doc = self.nlp(path)
            self.calculate_dsh_mention_attributes(doc)

            if verbose:
                self.print_spans(doc)

            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions
        
        return global_mentions


class PronounLemmaCorrector(object):
    def __init__(self):
        self.name = 'pronoun_lemma_corrector'

    def __call__(self, doc):
        for token in doc:
            if token.lower_ in ['she', 'her', 'herself']:
                token.lemma_ = token.lower_
        return doc


if __name__ == "__main__":
    dsha = DSHAnnotator()
    dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test/files/corpus')