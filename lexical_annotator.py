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

# TODO factorise these classes into a single AnnotatorSequence parent and 
# various child classes that implement load_lexicon and other methods


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

            if name not in self.nlp.pipe_names:
                component = LexicalAnnotator(self.nlp, terms, self.attribute, label, name, merge=self.merge)
                self.nlp.add_pipe(component, last=True)
            else:
                print('-- ', name, 'exists already. Component not added.')
        
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
        matches = self.get_longest_matches(matches)
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

            # avoid adding entities twice, but CAREFUL make sure this doesn't stop several annotations being added to the same token sequence
            if entity not in doc.ents:
                doc.ents = list(doc.ents) + [entity]

        # Merge all entities
        # TO DO spaCy stores ALL matches so we get 'deliberate' and 'self-harm' annotated separately - fix
        if self.merge:
            for ent in doc.ents:
                if ent.label_ == self.label:
                    ent.merge(lemma=''.join([token.lemma_ + token.whitespace_ for token in ent]).strip())

        return doc

    def get_longest_matches(self, matches):
        """
        Remove all shortest matching overlapping spans.
        :return: matches list of all longest matches only
        """
        offsets = [(match[1], match[2]) for match in matches]
        overlaps = {}
        for offset in offsets:
            o = [(i[0], i[1]) for i in offsets if i[0] >= offset[0] and 
                 i[0] <= offset[1] or i[1] >= offset[0] and 
                 i[1] <= offset[1] if (i[0], i[1]) != offset and
                 (i[0], i[1]) and (i[0], i[1]) not in overlaps]
            if len(o) > 0:
                overlaps[offset] = o
            
        overlapping_spans = [[k] + v for (k, v) in overlaps.items()]
        for os in overlapping_spans:
            longest_span = sorted(os, key=lambda x: x[1] - x[0], reverse=True)[0]
            for match in matches:
                start, end = match[1], match[2]
                # if it's not the longest match then chuck it out
                if (start, end) in os and (start != longest_span[0] or end != longest_span[1]):
                    matches.remove(match)
            
        return matches


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
                if line.startswith('#'):
                    continue
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
        for label in self.annotation_rules:
            lemma_sequences = self.annotation_rules[label]

            # Avoid component name clashes
            name = 'lex_' + label
            if name in self.nlp.pipe_names:
                name += '_'

            if name not in self.nlp.pipe_names:
                component = LemmaAnnotator(self.nlp, lemma_sequences, self.attribute, label, name, merge=self.merge)
                self.nlp.add_pipe(component, last=True)
            else:
                print('-- ', name, 'exists already. Component not added.')
        
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
        matches = self.get_longest_matches(matches)
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

            if entity not in doc.ents:
                try:
                    doc.ents = list(doc.ents) + [entity]
                except ValueError as e:
                    print('-- Warning: entity overlap for', entity)
                    print(e)

        # Merge all entities
        # TO DO spaCy stores ALL matches so we get 'deliberate' and 'self-harm' annotated separately - fix
        if self.merge:
            for ent in doc.ents:
                if ent.label_ == self.label:
                    ent.merge(lemma=''.join([token.lemma_ + token.whitespace_ for token in ent]).strip())

        return doc

    def get_longest_matches(self, matches):
        """
        Remove all shortest matching overlapping spans.
        :return: matches list of all longest matches only
        """
        offsets = [(match[1], match[2]) for match in matches]
        overlaps = {}
        for offset in offsets:
            o = [(i[0], i[1]) for i in offsets if i[0] >= offset[0] and 
                 i[0] <= offset[1] or i[1] >= offset[0] and 
                 i[1] <= offset[1] if (i[0], i[1]) != offset and
                 (i[0], i[1]) and (i[0], i[1]) not in overlaps]
            if len(o) > 0:
                overlaps[offset] = o
            
        overlapping_spans = [[k] + v for (k, v) in overlaps.items()]
        for os in overlapping_spans:
            longest_span = sorted(os, key=lambda x: x[1] - x[0], reverse=True)[0]
            for match in matches:
                start, end = match[1], match[2]
                # if it's not the longest match then chuck it out
                if (start, end) in os and (start != longest_span[0] or end != longest_span[1]):
                    matches.remove(match)
            
        return matches


class TokenSequenceAnnotatorSequence(object):
    
    def __init__(self, nlp, pin):
        pass
    
    def load_grammar(self):
        pass


if __name__ == '__main__':
    nlp = spacy.load('en_core_web_sm')

    print('Lexical Sequence Annotator')
    print('--------------------------')
    
    text = 'This patient, made an attempt to commit suicide, but shows signs of self-harm, but denies deliberate ' \
           'self-harm. However, see she has been cutting herself.'
    pin = 'T:/Andre Bittar/workspace/dsh_annotator/resources/dsh_lex.txt'
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
    pin = 'T:/Andre Bittar/workspace/dsh_annotator/resources/harm_action_lex.txt'
    lem_sa = LemmaAnnotatorSequence(nlp, pin, 'is_harm_action')
    lem_sa.load_lexicon()
    nlp = lem_sa.add_components()
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names)
    print('Annotations', [t._.is_harm_action or '_' for t in doc])
