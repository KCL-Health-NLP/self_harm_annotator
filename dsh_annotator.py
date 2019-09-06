# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 14:27:31 2018

@author: ABittar
"""

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

FWD_OFFSET = 10
BWD_OFFSET = 10

class DSHAnnotator:

    def __init__(self, verbose=False):
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
        """
        print(path, source_attribute, target_attribute, merge)
        if source_attribute == LEMMA:
            lsa = LemmaAnnotatorSequence(self.nlp, path, target_attribute, merge=merge)
        else:
            lsa = LexicalAnnotatorSequence(self.nlp, path, source_attribute, target_attribute, merge=merge)
        lsa.load_lexicon()
        self.nlp = lsa.add_components()

    def load_pronoun_lemma_corrector(self):
        component = LemmaCorrector()
        pipe_name = component.name

        if not pipe_name in self.nlp.pipe_names:
            self.nlp.add_pipe(component, last=True)
        else:
            print('-- ', pipe_name, 'exists already. Component not added.')

    def load_date_annotator(self):
        component = DateTokenAnnotator()
        pipe_name = component.name

        if not pipe_name in self.nlp.pipe_names:
            self.nlp.add_pipe(component, last=True)
        else:
            print('-- ', pipe_name, 'exists already. Component not added.')

    def load_detokenizer(self, path):
        """
        Load all detokenization rules.
        """
        print('-- Detokenizer')
        self.nlp = Detokenizer(self.nlp).load_detokenization_rules(path, verbose=self.verbose)

    def load_token_sequence_annotator(self, name):
        """
        Load all token sequence annotators.
        TODO allow for multiple annotators, cf. lemma and lexical annotators.
        TODO add path argument to specify rule file.
        """
        tsa = TokenSequenceAnnotator(self.nlp, name, verbose=self.verbose)
        if tsa.name not in self.nlp.pipe_names:
            self.nlp.add_pipe(tsa)

    def get_text(self):
        return self.text

    def normalise(self, text):
        """
        Add normalisation rules if we want to clean things up first
        """
        text = re.sub(' +', ' ', text)
        return text

    def annotate_text(self, text):
        self.text = text
        return self.nlp(text)

    def annotate_file(self, path):
        # TODO check for file in input
        # TODO check encoding
        f = open(path, 'r', encoding='Latin-1')
        self.text = f.read()

        if len(self.text) >= 1000000:
            print('-- Unable to process very long text text:', path)
            return None

        doc = self.nlp(self.text)
        
        return doc

    def has_negation_ancestor(self, cur_token, verbose=False):
        """
        Basic rule-based negation search in dependency tree.
        """
        if verbose:
            print('-- Detecting negations...', cur_token)

        if cur_token.lemma_ in ['report', 'say', 'claim', 'announce', 'insist']:
            for child in cur_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', cur_token)
                if child.dep_ == 'neg':
                    return True
            #return False

        elif cur_token.lemma_ in ['deny']:
            return True

        elif cur_token.pos_.startswith('N'):
            for child in cur_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', cur_token)
                if child.dep_ == 'neg' or child.lemma_ in ['no']:
                    return True
            #return False

        elif cur_token.pos_.startswith('V'):
            for child in cur_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', cur_token)
                if child.dep_ == 'neg':
                    return True
            #return False

        if cur_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.has_negation_ancestor(cur_token.head, verbose=verbose)

    def has_historical_ancestor(self, cur_token, verbose=False):
        if verbose:
            print('-- Detecting historical ancestors...', cur_token)
        
        if cur_token._.TIME == 'TIME':
            return True

        if cur_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.has_historical_ancestor(cur_token.head, verbose=verbose)

    def has_historical_dependent(self, cur_token, verbose=False):
        if verbose:
            print('-- Detecting historical modifiers...', cur_token)

        if cur_token.tag_ in ['VBG', 'VBN']:
            for child in cur_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', cur_token)
                if child.lower_ == 'had':
                    return True
                self.has_historical_dependent(child, verbose=verbose)

        if cur_token.pos_[0] in ['N', 'V']:
            for child in cur_token.children:
                if verbose:
                    print('  -- Checking child', child, 'of', cur_token)
                if child._.TIME == 'TIME':
                    return True
                self.has_historical_dependent(child, verbose=verbose)

        return False

    def has_hedging_ancestor(self, cur_token, verbose=True):
        if cur_token._.HEDGING == 'HEDGING':
            return True
        
        if cur_token.dep_ == 'ROOT':
            # ROOT
            return False
        
        return self.has_hedging_ancestor(cur_token.head, verbose=verbose)
    
    def has_hedging_dependent(self, cur_token, verbose=True):
        for child in cur_token.children:
            if child._.HEDGING == 'HEDGING':
                return True
            self.has_hedging_dependent(child, verbose=verbose)
        
        return False

    def has_hedging_noun_previous(self, doc, i, verbose=False):
        """ Check anywhere right up to the start of the sentence (
        as opposed to 5 previous tokens"""
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
    
    # This has a disastrous effect on results
    def has_past_tense_governor(self, curr_token):
        """ Check if governor is a past tense verb """
        return curr_token.head.tag_ in ['VBD', 'VBN', 'VHD', 'VHN', 'VVD', 'VVN']
    
    def has_propatt_ancestor(self, cur_token):
        """ Check if DSH mention has a propositional attitude ancestor"""
        if cur_token.head.pos_ == 'VERB':
            if cur_token.head.lemma_ in ['believe', 'desire', 'dream', 'feel', 'imagine', 'think', 'want', 'wish', 'wonder']:
                return True

        if cur_token.head.pos_ == 'NOUN':
            if cur_token.head.lemma_ in ['assumption', 'belief', 'feeling', 'desire', 'dream', 'idea', 'opinion', 'wish', 'view']:
                return True

        if cur_token.head._.DSH == 'NON_DSH':
            # e.g. suicidal thoughts   
            match = re.search('idea(tion)?|intent|thought', cur_token.head.lemma_, flags=re.I)
            return match is not None

        if cur_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.has_propatt_ancestor(cur_token.head)
    
    def is_reported_speech(self, cur_token):
        """ Check if the current node is governed by a reported speech verb 
        -- NOT IN USE
        """
        if cur_token.head._.RSPEECH == 'TRUE':
            return True

        if cur_token.dep_ == 'ROOT':
            # ROOT
            return False

        return self.is_reported_speech(cur_token.head.head)
    
    def is_section_header(self, doc, i, verbose=True):
        cur_sent = doc[i].sent
        end = len(cur_sent) - 1
        window = cur_sent[i:end].text
        if re.search(':', window) is not None:
            return True
        return False
    
    def is_singleton(self, doc, i):
        if doc[i].text == doc[i].sent.text:
            return True
        return False
    
    def is_definite(self, doc, i):
        for child in doc[i].children:
            if child.lemma_ in ['the', 'this', 'that', 'her']:
                return True
        return False
    
    def calculate_dsh_mention_attributes(self, doc, verbose=False):
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

        def get_longest_spans(offsets):
            """ Get a unique list of all overlapping span offsets """
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
            with open('Z:/Andre Bittar/Projects/KA_Self-harm/data/batch_err.log', 'a') as b_err:
                print('Unable to create XML file:', ehost_pout, file=b_err)
            b_err.close()
            return root

        if verbose:
            print(pxmlstr.toprettyxml(indent='\t'), file=sys.stderr)

        # Write to file
        #tree = ET.ElementTree(root)
        #tree.write(ehost_pout, encoding="utf-8", xml_declaration=True)
        open(ehost_pout, 'w').write(pxmlstr.toprettyxml(indent='\t'))
        if verbose:
            print('-- Wrote EHOST file: ' + ehost_pout, file=sys.stderr)

        return root

    def process(self, path, write_output=True):
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
        self.verbose = verbose
        if self.verbose:
            print('-- Processing text string:', text, file=sys.stderr)
        
        global_mentions = {}
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
            self.write_ehost_output('test.txt', mentions, verbose=self.verbose)
        
        return global_mentions


class LemmaCorrector(object):
    def __init__(self):
        self.name = 'pronoun_lemma_corrector'

    def __call__(self, doc):
        for token in doc:
            if token.lower_ in ['she', 'her', 'herself', 'themselves']:
                token.lemma_ = token.lower_
            if token.lower_ == 'overdoses':
                token.lemma_ = 'overdose'
        return doc


class DateTokenAnnotator(object):
    def __init__(self):
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
    if False:
        dsha = DSHAnnotator(verbose=False)
        #dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system/files/corpus')
        dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev/files/corpus', write_output=True)
        #dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev/files/corpus/01-07-2011_29365502.txt', write_output=True)
    else:
        dsha = DSHAnnotator(verbose=True)
        dsh_annotations = dsha.process_text(text, 'text_001', write_output=False, verbose=True)

    #pin = 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/10015033/corpus/2008-02-21_12643289_30883.txt'
    #dsh_annotations = dsha.process(pin, verbose=True, write_output=True)
