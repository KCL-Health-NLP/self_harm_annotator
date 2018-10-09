# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 11:49:14 2018

@author: ABittar
"""

import spacy
import sys

from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Span, Token
from spacy.symbols import LEMMA

# TODO factorise these classes into a single AnnotatorSequence parent and various child classes that implement
# load_lexicon and other methods


class LexicalAnnotatorSequence(object):
    """
    Creates a set of new pipeline components that annotate tokens accoring to
    a terminology list. Match is only performed on textual surface form.
    """
    def __init__(self, nlp, pin, attribute, merge=False):
        self.nlp = nlp
        self.pin = pin
        self.attribute = attribute
        self.annotation_rules = {}
        self.merge = merge

    def load_lexicon(self):
        n = 1
        with open(self.pin, 'r') as fin:
            for line in fin:
                try:
                    term, label = line.split('\t')
                except Exception as e:
                    print('-- Warning: syntax error in rule file ' + self.pin + ' at line', n, file=sys.stderr)
                term = term.strip()
                label = label.strip()
                terms = self.annotation_rules.get(label, [])
                terms.append(term)
                self.annotation_rules[label] = terms
                n += 1
        fin.close()

    def get_labels(self):
        return self.annotation_rules.keys()

    def get_annotation_rules(self):
        return self.annotation_rules

    def add_components(self, merge=False):
        for label in self.annotation_rules:
            terms = self.annotation_rules[label]

            # Avoid component name clashes
            name = 'lex_' + label
            if name in self.nlp.pipe_names:
                name += '_'

            component = LexicalAnnotator(self.nlp, terms, self.attribute, label, name, merge=self.merge)
            self.nlp.add_pipe(component, last=True)
        
        return self.nlp


class LexicalAnnotator(object):
    """
    Initialises a single new component that annotates tokens accoring to a 
    terminology list. Match is only performed on textual surface form.
    """
    
    def __init__(self, nlp, terms, attribute, label, name, merge=False):
        self.name = name
        self.nlp = nlp
        self.label = label  # get entity label ID
        self.attribute = attribute
        self.merge = merge

        patterns = [self.nlp(text) for text in terms]
        self.matcher = PhraseMatcher(self.nlp.vocab)
        self.matcher.add(label, None, *patterns)
        Token.set_extension(attribute, default=False, force=True)

    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []
        Token.set_extension('tense', default=False, force=True)
        for _, start, end in matches:
            entity = Span(doc, start, end, label=self.nlp.vocab.strings[self.label])
            spans.append(entity)
            # Copy tense attribute to entity (for DSH annotator)
            tense = '_'
            for token in entity:
                token._.set(self.attribute, self.label)
                if token.pos_ == 'VERB':
                    tense = token.tag_
            for token in entity:
                token._.set('tense', tense)

            doc.ents = list(doc.ents) + [entity]

        # Merge all entities
        if self.merge:
            for ent in doc.ents:
                ent.merge()

        return doc


class LemmaAnnotatorSequence(object):
    """
    Creates a set of new pipeline components that annotate tokens accoring to
    a terminology list. Match is only performed on token lemma.
    """
    def __init__(self, nlp, pin, attribute, ignore_case=True, merge=False):
        self.nlp = nlp
        self.pin = pin
        self.attribute = attribute
        self.annotation_rules = {}
        self.ignore_case = ignore_case
        self.merge = merge

    def load_lexicon(self):
        n = 1
        with open(self.pin, 'r') as fin:
            for line in fin:
                try:
                    term, label = line.split('\t')
                except Exception as e:
                    raise ValueError('-- Error: syntax error in rule file ' + self.pin + ' at line', n)
                term = term.strip()
                label = label.strip()
                terms = self.annotation_rules.get(label, [])
                terms.append(term)
                self.annotation_rules[label] = terms
                n += 1
        fin.close()

    def get_labels(self):
        return self.annotation_rules.keys()

    def get_annotation_rules(self):
        return self.annotation_rules

    def add_components(self):
        print(self.annotation_rules, file=sys.stderr)
        for label in self.annotation_rules:
            print(label, file=sys.stderr)
            lemma_sequences = self.annotation_rules[label]

            # Avoid component name clashes
            name = 'lex_' + label
            if name in self.nlp.pipe_names:
                name += '_'

            component = LemmaAnnotator(self.nlp, lemma_sequences, self.attribute, label, name, merge=self.merge)
            self.nlp.add_pipe(component, last=True)
        
        return self.nlp


class LemmaAnnotator(object):

    def __init__(self, nlp, lemma_sequences, attribute, label, name, merge=False):
        self.name = name
        self.nlp = nlp
        self.label = label
        self.attribute = attribute
        self.matcher = Matcher(self.nlp.vocab)
        self.merge = merge

        # Build patterns from sequences of lemmas read from the lexicon file
        for lemmas in lemma_sequences:
            pattern = []
            for lemma in lemmas.split():
                pattern.append({LEMMA: lemma})
            self.matcher.add(label, None, pattern)

        Token.set_extension(attribute, default=False, force=True)
        
    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []
        Token.set_extension('tense', default=False, force=True)
        for _, start, end in matches:
            entity = Span(doc, start, end, label=self.nlp.vocab.strings[self.label])
            spans.append(entity)
            # Copy tense attribute to entity (for DSH annotator)
            tense = '_'
            for token in entity:
                token._.set(self.attribute, self.label)
                if token.pos_ == 'VERB':
                    tense = token.tag_
            for token in entity:
                token._.set('tense', tense)

            doc.ents = list(doc.ents) + [entity]

        # Merge all entities
        if self.merge:
            for ent in doc.ents:
                ent.merge()

        return doc


class TokenSequenceAnnotatorSequence(object):
    
    def __init__(self, nlp, pin):
        pass
    
    def load_grammar(self):
        pass


if __name__ == '__main__':
    nlp = spacy.load('en')

    print('Lexical Sequence Annotator')
    print('--------------------------')
    
    text = 'This patient, made an attempt to commit suicide, but shows signs of self-harm, but denies deliberate ' \
           'self-harm. However, see she has been cutting herself.'
    pin = 'T:/Andre Bittar/workspace/ka_dsh/resources/dsh_lex.txt'
    lsa = LexicalAnnotatorSequence(nlp, pin, 'is_dsh')
    lsa.load_lexicon()
    nlp = lsa.add_components()
    doc = nlp(text)
    
    print('Pipeline   ', nlp.pipe_names)
    print('Annotations', [t._.is_dsh for t in doc])
    print()

    print('Lemma Sequence Annotator')
    print('------------------------')
       
    text = 'This patient scratches herself and cuts up her arms.'
    pin = 'T:/Andre Bittar/workspace/ka_dsh/resources/harm_V_lex.txt'
    lem_sa = LemmaAnnotatorSequence(nlp, pin, 'is_harm_action')
    lem_sa.load_lexicon()
    nlp = lem_sa.add_components()
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names)
    print('Annotations', [t._.is_harm_action or '_' for t in doc])
