# -*- coding: utf-8 -*-
"""
    Lexical Annotators
    
    This is a spaCy pipeline component to add lexical annotations to tokens in 
    a document according to a specified external lexicon file. A lexicon file
    is loaded when the component is added to the pipeline and applied when the 
    pipeline is executed.
    
    # TODO factorise these classes into a single AnnotatorSequence parent and 
    # various child classes that implement load_lexicon() and other methods
    # TODO implement TokenSequenceAnnotator

"""

import spacy
import sys

from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Span, Token
from spacy.symbols import LEMMA, LOWER

__author__ = "André Bittar"
__copyright__ = "Copyright 2020, André Bittar"
__credits__ = ["André Bittar"]
__license__ = "GPL"
__email__ = "andre.bittar@kcl.ac.uk"


class LexicalAnnotatorSequence(object):
    """
    Lexical Annotator Sequence
    
    Create a set of new pipeline components that annotate tokens according to
    a word list provided in an external file. Match is only performed on textual
    surface form.
    """
    
    def __init__(self, nlp, pin, source_attribute, target_attribute, merge=False):
        """
        Create a new LexicalAnnotatorSequence instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
            - pin: str; the input path of a lexical rule file.
            - source_attribute: spaCy symbol; the token attribute to match
              on (e.g. LEMMA).
            - target_attribute: spaCy symbol; the token attribute to add the 
              lexical annotations to (e.g. TAG, or custom attribute LA, DSH).
            - merge: bool; merge annotated spans into a single span.
        """
        self.nlp = nlp
        self.pin = pin
        self.source_attribute = source_attribute
        self.target_attribute = target_attribute
        self.annotation_rules = {}
        self.merge = merge

    def load_lexicon(self):
        """
        Load the lexical rules from the input file.
        """
        n = 1
        with open(self.pin, 'r') as fin:
            for line in fin:
                # ignore comments
                if line.strip()[0] == '#':
                    continue
                try:
                    term, label = line.split('\t')
                except Exception as e:
                    print('-- Warning: syntax error in rule file ' + self.pin + ' at line', n, file=sys.stderr)
                    print(e, file=sys.stderr)
                term = term.strip()
                label = label.strip()
                terms = self.annotation_rules.get(label, [])
                terms.append(term)
                self.annotation_rules[label] = terms
                n += 1
        fin.close()

    def get_labels(self):
        """
        Get the labels.
        
        Return: dict_keys; the labels that are added to matched tokens.
        """
        return self.annotation_rules.keys()

    def get_annotation_rules(self):
        """
        Get the annotation rules.
        
        Return: dict; a dictionary containing all loaded lexical annotation rules.
        """
        return self.annotation_rules

    def add_components(self, merge=False):
        """
        Add components to the pipeline.
        
        Arguments:
            - merge: bool; merge annotated spans into a single span.

        Return:
            - self.nlp: spaCy Lang; the loaded spaCy pipeline object with added 
                        annotation rules.
        """
        for label in self.annotation_rules:
            terms = self.annotation_rules[label]

            # Avoid component name clashes
            name = 'lex_' + label
            if name in self.nlp.pipe_names:
                name += '_'

            if name not in self.nlp.pipe_names:
                component = LexicalAnnotator(self.nlp, terms, self.source_attribute, self.target_attribute, label, name, merge=self.merge)
                self.nlp.add_pipe(component, last=True)
            else:
                print('-- ', name, 'exists already. Component not added.')
        
        return self.nlp


class LexicalAnnotator(object):
    """
    Lexical Annotator
    
    Initialises a single new spaCy pipeline component that annotates tokens 
    accoring to a word list. Match is only performed on textual surface form.
    """
    
    def __init__(self, nlp, terms, source_attribute, target_attribute, label, name, merge=False):
        """
        Create a new LexicalAnnotator instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
            - terms: list; the terms to be annotated.
            - source_attribute: spaCy symbol; the token attribute to match
              on (e.g. LEMMA).
            - target_attribute: spaCy symbol; the token attribute to add the 
              lexical annotations to (e.g. TAG, or custom attribute LA, DSH).
            - label: str; the label to add to the tokens' target attribute.
            - name: str; the name of the pipeline component.
            - merge: bool; merge annotated spans into a single span.
        """
        self.name = name
        self.nlp = nlp
        self.label = label  # get entity label ID
        self.target_attribute = target_attribute
        self.merge = merge

        patterns = [self.nlp(text) for text in terms] # using make_doc as nlp() causes UseWarning saying that it may be much slower for tokenizer-based attributes (ORTH, LOWER)
        self.matcher = PhraseMatcher(self.nlp.vocab, attr=source_attribute)
        self.matcher.add(label, None, *patterns)
        Token.set_extension(target_attribute, default=False, force=True)

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
                token._.set(self.target_attribute, self.label)
                if token.pos_ == 'VERB':
                    tense = token.tag_
            for token in entity:
                token._.set('tense', tense)

            # avoid adding entities twice, but CAREFUL make sure this doesn't stop several annotations being added to the same token sequence
            if entity not in doc.ents:
                # check for overlap
                if self.check_entity_overlap(doc, entity):
                    doc.ents = list(doc.ents) + [entity]

        # Merge all entities
        # TO DO spaCy stores ALL matches so we get 'deliberate' and 'self-harm' annotated separately - fix
        if self.merge:
            print('-- Merging spans...', file=sys.stderr)
            for ent in doc.ents:
                if ent.label_ == self.label:
                    ent.merge(lemma=''.join([token.lemma_ + token.whitespace_ for token in ent]).strip())

        return doc

    def check_entity_overlap(self, doc, entity):
        """
        Check the document for overlapping entities.
        
        Arguments:
            - doc: spaCy Doc; a spaCy document instance.
            - entity: spaCy Span; an entity span to check for overlap.
        
        Return: bool; True if entities are foudn that overlap with entity, else False
        """
        ent_offsets = [(ent.start, ent.end) for ent in doc.ents]
        for (start, end) in ent_offsets:
            # no overlap, no problem
            if entity.start > end:
                continue
            if entity.end < start:
                continue
            # overlap - retain the new entity if it is longer
            if (entity.end - entity.start) > (end - start):
                #print('-- Replacing entity', ent.start, ent.end, ent, 'with', entity.end, entity.start, entity, file=sys.stderr)
                new_ents = [ent for ent in doc.ents if ent.start != start and ent.end != end]
                doc.ents = new_ents
                return True
            if (entity.end - entity.start) == (end - start):
                print('-- Warning: exactly overlapping entities:', entity.end, entity.start, entity, '&', start, end, doc[start:end], file=sys.stderr)
        return False

    def get_longest_matches(self, matches):
        """
        Remove all shortest matching overlapping spans.
        
        Arguments:
            - matches: list; a list of matched entities.
        
        Return:
            - matches: list; all longest matches only.
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
    Lemma Annotator Sequence
    
    Creates a set of new spaCy pipeline components that annotate tokens accoring
    to a word list. Match is only performed on token lemma.
    """
    def __init__(self, nlp, pin, attribute, ignore_case=True, merge=False):
        """
        Create a new LemmaAnnotatorSequence instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
            - pin: str; the input path of a lexical rule file.
            - attribute: spaCy symbol; the token attribute to add the lexical 
                         annotations to (e.g. TAG, or custom attribute LA, DSH).
            - ignore_case: bool; make matching case-insensitive
            - merge: bool; merge annotated spans into a single span.
        """
        self.nlp = nlp
        self.pin = pin
        self.attribute = attribute
        self.annotation_rules = {}
        self.ignore_case = ignore_case
        self.merge = merge

    def load_lexicon(self):
        """
        Load the lexical rules from the input file.
        """
        n = 1
        with open(self.pin, 'r') as fin:
            for line in fin:
                # ignore comments
                if line.strip()[0] == '#':
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
        """
        Get the labels.
        
        Return: dict_keys; the labels that are added to matched tokens.
        """
        return self.annotation_rules.keys()

    def get_annotation_rules(self):
        """
        Get the annotation rules.
        
        Return: dict; a dictionary containing all loaded lexical annotation rules.
        """
        return self.annotation_rules

    def add_components(self):
        """
        Add component to the pipeline.
        
        Arguments:
            - merge: bool; merge annotated spans into a single span.
            
        Return:
            - self.nlp: spaCy Lang; the loaded spaCy pipeline object with added 
                        annotation rules
        """
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
    """
    Lemma Annotator
    
    Initialises a single new spaCy pipeline component that annotates tokens 
    according to a word list. Match is only performed on word lemma.
    """

    def __init__(self, nlp, lemma_sequences, attribute, label, name, merge=False):
        """
        Create a new LemmaAnnotator instance.
        
        Arguments:
            - nlp: spaCy Language; a spaCy text processing pipeline instance.
            - lemma_sequences: list; the lemmas to be annotated.
            - attribute: spaCy symbol; the token attribute to add the 
              lexical annotations to (e.g. TAG, or custom attribute LA, DSH).
            - label: str; the label to add to the tokens' target attribute.
            - name: str; the name of the pipeline component.
            - merge: bool; merge annotated spans into a single span.
        """
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

            # avoid adding entities twice, but CAREFUL make sure this doesn't stop several annotations being added to the same token sequence
            if entity not in doc.ents:
                # check for overlap
                if self.check_entity_overlap(doc, entity):
                    doc.ents = list(doc.ents) + [entity]

        # Merge all entities
        # TO DO spaCy stores ALL matches so we get 'deliberate' and 'self-harm' annotated separately - fix
        if self.merge:
            print('-- Merging spans...', file=sys.stderr)
            for ent in doc.ents:
                if ent.label_ == self.label:
                    ent.merge(lemma=''.join([token.lemma_ + token.whitespace_ for token in ent]).strip())

        return doc

    def check_entity_overlap(self, doc, entity):
        """
        Check the document for overlapping entities.
        
        Arguments:
            - doc: spaCy Doc; a spaCy document instance.
            - entity: spaCy Span; an entity span to check for overlap.
        
        Return: bool; True if entities are foudn that overlap with entity, else False
        """
        ent_offsets = [(ent.start, ent.end) for ent in doc.ents]
        for (start, end) in ent_offsets:
            # no overlap, no problem
            if entity.start > end:
                continue
            if entity.end < start:
                continue
            # overlap - retain the new entity if it is longer
            if (entity.end - entity.start) > (end - start):
                #print('-- Replacing entity', ent.start, ent.end, ent, 'with', entity.end, entity.start, entity, file=sys.stderr)
                new_ents = [ent for ent in doc.ents if ent.start != start and ent.end != end]
                doc.ents = new_ents
                return True
            if (entity.end - entity.start) == (end - start):
                print('-- Warning: exactly overlapping entities:', entity.end, entity.start, entity, '&', start, end, doc[start:end], file=sys.stderr)
        return False

    def get_longest_matches(self, matches):
        """
        Remove all shortest matching overlapping spans.
        
        Arguments:
            - matches: list; a list of matched entities.
        
        Return:
            - matches: list; all longest matches only.
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
    """
    # TODO implement
    """
    
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
    pin = 'resources/dsh_lex.txt'
    lsa = LexicalAnnotatorSequence(nlp, pin, LOWER, 'is_dsh')
    lsa.load_lexicon()
    nlp = lsa.add_components()
    doc = nlp(text)
    
    print('Pipeline   ', nlp.pipe_names)
    print('Annotations', [t._.is_dsh for t in doc])
    print()

    print('Lemma Sequence Annotator')
    print('------------------------')
    
    text = 'This patient scratches herself and cuts up her arms.'
    pin = 'resources/harm_action_lex.txt'
    lem_sa = LemmaAnnotatorSequence(nlp, pin, 'is_harm_action')
    lem_sa.load_lexicon()
    nlp = lem_sa.add_components()
    doc = nlp(text)

    print('Pipeline   ', nlp.pipe_names)
    print('Annotations', [t._.is_harm_action or '_' for t in doc])
