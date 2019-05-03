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
from spacy.symbols import LEMMA
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError


class DSHAnnotator:

    def __init__(self, verbose=False):
        self.nlp = spacy.load('en')
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
        self.load_lexicon('./resources/dsh_sequence_lex.txt', LEMMA, 'DSH', merge=True)
        #self.load_lexicon('./resources/dsh_lex_lemma.txt', LEMMA, 'DSH', merge=True)
        self.load_lexicon('./resources/time_lex.txt', LEMMA, 'TIME')
        self.load_lexicon('./resources/current_lex.txt', LEMMA, 'TIME')
        self.load_lexicon('./resources/negation_lex.txt', LEMMA, 'NEG')
        self.load_lexicon('./resources/modality_lex.txt', LEMMA, 'MODALITY')
        self.load_lexicon('./resources/hedging_lex.txt', LEMMA, 'HEDGING')
        self.load_lexicon('./resources/body_part_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/harm_V_lex.txt', LEMMA, 'LA')
        self.load_lexicon('./resources/reported_speech_lex.txt', LEMMA, 'RSPEECH')
        
        # Load token sequence annotators
        self.load_token_sequence_annotator(None)
    
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
        # TODO check encoding
        f = open(path, 'r', encoding='Latin-1')
        self.text = f.read()
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
        for i in range(len(doc)):
            if doc[i]._.DSH in ['DSH', 'NON_DSH']:
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
                start = i - 5
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
                        if not self.is_definite(doc, i) and token._.NEG == 'NEG':
                            doc[i]._.NEG = 'NEG'
                        if token._.TIME == 'TIME':
                            doc[i]._.TIME = 'TIME'
                        if token._.MODALITY == 'MODALITY':
                            doc[i]._.MODALITY = 'MODALITY'
                        if token._.HEDGING == 'HEDGING':
                            doc[i]._.HEDGING = 'HEDGING'

        # Hack: get attributes from window of 5 tokens after DSH mention in the same sentence
        for i in range(len(doc)):
            if doc[i]._.DSH in ['DSH', 'NON_DSH']:
                curr_sent = doc[i].sent
                end = i + 5
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
                        if token._.TIME == 'TIME':
                            doc[i]._.TIME = 'TIME'
                        if token._.MODALITY == 'MODALITY':
                            if not found_CCONJ:
                                doc[i]._.MODALITY = 'MODALITY'
                        if token._.HEDGING == 'HEDGING':
                            if not found_CCONJ:
                                doc[i]._.HEDGING = 'HEDGING'

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
        s += '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format('INDEX', 'WORD', 'LEMMA', 'POS1', 'POS2', 'HEAD', 'DEP')

        cext = set()        
        for a in doc.user_data:
            cext.add(a[1])

        cext = sorted(cext)

        for a in cext:
            s += '{:<10}'.format(a)

        s += '\n'

        s += '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format('-----', '----', '-----', '----', '----', '----', '----')

        for a in cext:
            s += '{:<10}'.format('-' * len(a))

        print(s, file=sys.stderr)
        
        for token in doc:
            s = '{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format(token.i, token.text, token.lemma_, token.tag_, token.pos_, token.head.i, token.dep_)
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
                if token._.TIME == 'TIME':
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
                if token._.TIME == 'TIME':
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
        root.attrib['textSource'] = os.path.basename(os.path.splitext(pin.replace('.knowtatot.xml', ''))[0] + '.txt')

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

    def process(self, path, verbose=False, write_output=True):
        global_mentions = {}

        if os.path.isdir(path):
            files = os.listdir(path)
            
            for f in files:
                pin = os.path.join(path, f)
                if verbose:
                    print('-- Processing file:', pin, file=sys.stderr)
                # Annotate and print results
                doc = self.annotate_file(pin)
                self.calculate_dsh_mention_attributes(doc)
                
                if verbose:
                    self.print_spans(doc)
                
                mentions = self.build_ehost_output(doc)
                global_mentions[f + '.knowtator.xml'] = mentions

                if write_output:
                    self.write_ehost_output(pin, mentions, verbose=verbose)
                
        elif os.path.isfile(path):
            print('-- Processing file:', path, file=sys.stderr)
            doc = self.annotate_file(path)
            self.calculate_dsh_mention_attributes(doc)
            
            if verbose:
                self.print_spans(doc)
            
            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions

            if write_output:
                self.write_ehost_output(path, mentions, verbose=verbose)

        else:
            print('-- Processing text string:', path, file=sys.stderr)
            doc = self.nlp(path)
            self.calculate_dsh_mention_attributes(doc)

            if verbose:
                self.print_spans(doc)

            mentions = self.build_ehost_output(doc)
            key = os.path.basename(path)
            global_mentions[key] = mentions

            if write_output:
                self.write_ehost_output('test.txt', mentions, verbose=verbose)
        
        return global_mentions
    
    
    def process_text(self, text, text_id, verbose=False, write_output=False):
        if verbose:
            print('-- Processing text string:', text, file=sys.stderr)
        
        global_mentions = {}
        doc = self.nlp(text)
        self.calculate_dsh_mention_attributes(doc)

        if verbose:
            self.print_spans(doc)

        mentions = self.build_ehost_output(doc)
        
        global_mentions[text_id] = mentions

        if write_output:
            self.write_ehost_output('test.txt', mentions, verbose=verbose)
        
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
    dsha = DSHAnnotator()
    #dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system/files/corpus')
    #dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev/files/corpus')

    text = 'Has no history of taking overdoses'
    text = 'risk of self-harm'
    text = 'She is taking multiple overdoses in the past'
    text = 'She took overdoses a long time ago'
    text = 'family history of self-harm'
    text = 'She wanted to hit herself'
    text = 'She did not self-harm'
    text = 'cuts could be due to self-harm'
    text = 'has a high risk of cutting herself'
    text = 'she took an overdose in 1996'
    text = 'chronic thoughts of self-harm'
    text = 'her father has chronic self-harm'
    text = 'she had cut herself'
    text = 'she did self-imolation in the past'
    text = 'no acts of self-harm'
    text = 'she did not harm herself'
    text = 'has a history of self-abuse'
    text = 'has a history of taking multiple overdoses in the past'
    text = 'She does not report having had actual self-harm'
    text = 'She says she has never cut her arm'
    text = 'She does not report having had actual suicidal thoughts, intent or plans (and cites family reasons as being protective) as such.'
    text = 'There is no history of deliberate self-harm except for one occasion when she reports having attempted to walk into the middle of the road (but this was when she was manic in the context of grandiose thoughts)'
    text = """e.g. sees sister regularly, goes to Effra day centre three days a week 


Risk history:

Harm to self: DSH & suicide attempts; poor self-care; untreated physical illness; vulnerability to exploitation"""
    text = 'In November 2006- Whilst in PICU at  ZZZZZ  Hospital- she described suicidal thoughts, low mood and talked about strangling babies.'
    text = 'she has a history of self-harm'
    text = 'she cut herself when she was 32 years old'
    text = 'Her mother has suffered from depression and attempted suicide in the past but is currently well.'
    text = 'She would cut herself numerous times'
    text = 'She has had five psychiatric admissions precipitated by suicidal and self-harm behaviour.'
    text = 'Self-harm'
    text = 'suicide (self harm) : with a lot of room for the very lovely self harm'
    text = "Sertraline 50mg OD, has been taking this for last few days"
    text = 'She has reported self-harm ideation'
    text = 'Instances of deliberate self-harm in 2002.'
    text = 'She had recently taken an overdose of Olanzapine'
    text = 'Took OD because wanted to die due to children being taken from her.'
    text = 'She has scratches on her arms'
    text = '- History of self-harms (superficial cuts on forearms) according to ZZZZZ last time about 6 months ago.'
    text = 'She was reported to be banging her head on the fence'
    text = 'She has a history of throwing herself in front of a bus.'
    text = 'On Monday night ZZZZZ had tied a shirt and a dressing gown together and was planning to attach this to the door handle and hang herself.'
    text = 'ZZZZZ was clear that she has not had any other thoughts of suicide since Monday.'
    text = 'The reason for the recall is that she had threatened to induce her labour herself to staff and given her history of trying to asphyxiate herself in the 20th week of pregnancy the threat to do this was taken seriously.'
    text = """Risperidone 6mg OD
Allergic to Penicillin"""

    # 28.01.2019
    text = """Does not see a future for herself

Reluctant to talk about stressors and triggers that led her to attempt suicide
mentioned briefly about financial problems"""
    text = 'Denied she has said she wanted to cut the baby out, said she had asked about what would happen to the baby if she killed herself and if the doctors would cut the baby out if she tried to commit suicide.'
    text = 'She cried during our meeting, talking about thinking of overdosing.'
    text = 'At one point she told the neighbours she was going to kill herself and stated that her friend had poisoned their water pipes.'
    text = 'There is no history of suicidal thoughts being expressed; command hallucinations to harm her or deliberate self harm acts.'
    text = 'Impact: Moderate to self but given that she is pregnant OD could cause serious harm to babay'
    text = 'In terms of risks, there is a noted history of self harm in the past. As mentioned, she reports a planned overdose in the context of depression and suicidal intent at the age of 16, which was incidentally discovered by her mother.'
    text = 'As mentioned, she reports a planned overdose in the context of depression and suicidal intent at the age of 16, which was incidentally discovered by her mother.'
    text = 'Took OD because wanted to die due to children being taken from her.'
    text = 'ZZZZZ  -  risk of aggression, self neglect and non serious self harm when unwell noted.'
    text = 'Risk of intentional harm: moderate at the moment due to ambivalent suicide ideation, and previous high risk suicidal behaviour prior to admission (lying under a bus )'
    text = 'She has not prevoiously attempted suicide since 2006.'
    text = "ZZZZZ  acknowledged that her decision to hang herself was because she was 'angry and raging' with both  QQQQQ  and her mother."
    text = 'However, she still regrets that she did not succeed and still thinks about doing it and would use same method with OD.'
    text = 'Referred by PLN - patient admitted earlier today to Lewisham RATU after taking an OD of Sibutramine 20mg x17 tabs + Acamprosate 333mg x 20tabs'
    text = 'On Monday night,  ZZZZZ  had tied a shirt and a dressing gown together and was planning to attach this to the door handle and hang herself.'
    text = 'She does not fully understand the severity of her overdose and is not willing to be admitted to a psychiatric ward.'    
    text = 'She said that she never intended to jump out of the window but was just opening it.'
    text = 'ZZZZZ  was not able to pinpoint a direct trigger for the suicide attempt and says she has just been feeling more depressed over the past week.'
    text = 'She feels she could not trust herself if she were discharged from hospital now, as even now regrets s that the overdose did not work. Social Services involved re 12-year-old child.'
    text = 'She does not regret the suicide attempt but feels guilty because of her daughter.'
    text = 'She has suicidal thoughts about taking an overdose.'
    text = 'She admitted to recurrent suicidal thoughts about taking an overdose or jumping in front of a moving car and also admitted to fleeting thoughts about smothering her baby.'
    text = 'Poor coping skills - likely to show impulsive behaviour (self-harm or fire-setting) when stressed.'
    text = """Risks
Self neglect
Self harm
She is vulnerable both physical, financial and sexually for exploitation. She has the history of self harm.
"""
    text = 'Current or past risk of suicide (overdose, self harm, starvation, jumping from height etc) : self harm, ( cutting her wrist with table knife)'
    text = 'She described two previous psychiatric hospital admissions following suicide attempts, and possibly drug-induced psychosis, and one episode of depressed mood and psychosis (probably a psychotic depression) in prison custody in 2005.'
    text = "She stated that she had only refused treatment because she was 'bored, I wanted to go out for a cigarette'. She stated that the 'OD was not that bad, I'm ok, the baby's kicking, its fine', grossly minimising the impact and seriousness of this act."
    text = 'She is 6 months pregnant and has taken a massive overdose with intention to end her life.'
    text = '2006 - Overdose with 40 tabs of Sertraline, wanted to kill herself. She then rang her mom who called ambulance.'
    text = 'In terms of risks, whilst she has developed pessimistic and negative thoughts during the depressive periods, there has been no actual self harm or suicidal thoughts.'
    text = 'Drug induced psychosis 1991 Bexley Health hospital - OD/cut wrist - voluntary ? 2-3 week admission.'
    text = "ZZZZZ   ZZZZZ  told us she was admitted to Bexley Hospital, informally, at the age of 16 following a suicide attempt and a 'drug psychosis' secondary to cannabis abuse."
    text = '20/09/99: Overdose of methadone, paroxetine, zopiclone, and alcohol.'
    text = '1998 - Tried to hang herself but cord broke down. She was depressed but not on medications.'
    text = "Multiple admissions related to drug induced psychosis. Last admission in Sep' 06 with overdose of Sertraline."
    text = 'Previous attempted overdose approximately two months ago (48 tablets including Quetiapine)'
    text = "Dr Wuyts concluded that Ms  ZZZZZ 's current mental state is characterised by elaborate symptoms of depression, coinciding with minor paranoid ideation, history of DSH and social problems and a first degree family history of schizophrenia."
    text = 'Self: previous possible sexual exploitation- inviting men back to her flat to use drugs, risk assessment notes history of suicidal ideation and acts including overdose, little detail'
    text = """No risk when stable as she is now
Had 2 suicide attempts during psychotic episode in 2007 - One of them was trying to cut her wrists and then jump out of the window, on another occasion attempted OD with painkillers and alcohol
"""
    text = "Other concerns were around  ZZZZZ 's ability to care for the child, her dissociation and self-harm and her issues around the child being a girl."
    text = 'ZZZZZ  has reported no current thoughts of deliberate self harm but disclosed past self harm when initially became unwell aged 25 years.'
    text = 'She experienced anhedonia, was very negative about the future and had suicidal thoughts and self harmed.'
    
    text = 'She has a tendency to self-harm.'
    text = '2 previous overdoses with suicidal intent.'
    text = 'Overall, it appears that these suicidal thoughts and act (when she was aged 16), appears to have occurred in the context of depressive mood, possibly precipitated by social crisis.'
    text = 'Her planned overdose did not happen'
    text = 'ZZZZZ  admitted to POS, partner reported patient self- harm via cut to her arm and neck on a number of times after a verbal argument.'
    text = 'History of self-harm at 16'
    text = 'H/o self-harm'
    text = 'She has made eight attempts to kill herself'
    text = 'Risperidone 40 mgs OD'
    text = 'Overdose on Monday'
    
    dsh_annotations = dsha.process_text(text, 'text_001', verbose=True, write_output=False)
    
    #pin = 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/10015033/corpus/2008-02-21_12643289_30883.txt'
    #dsh_annotations = dsha.process(pin, verbose=True, write_output=True)
