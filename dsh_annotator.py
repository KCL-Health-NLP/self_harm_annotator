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


class DSHAnnotator:

    def __init__(self, verbose=False):
        self.nlp = spacy.load('en')
        self.text = None
        self.verbose = verbose

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
        print('-- Checking for previous hedging noun...')
        for j in range(end, start, -1):
            token = doc[j]
            if token.pos_[0] == 'N' and not token._.DSH:
                if token._.HEDGING == 'HEDGING':
                    return True

        return False
    
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
    
    def calculate_dsh_mention_attributes(self, doc):
        # Hack: get attributes from window of 5 tokens before DSH mention
        for i in range(len(doc)):
            if doc[i]._.DSH in ['DSH', 'NON_DSH']:
                if self.has_negation_ancestor(doc[i]):
                    print('-- Negation detected for', doc[i])
                    doc[i]._.NEG = 'NEG'
                
                if self.has_hedging_noun_previous(doc, i):
                    doc[i]._.HEDGING = 'HEDGING'
                
                if self.is_singleton(doc, i):
                    # mark as HEDGING (NON-RELEVANT)
                    doc[i]._.HEDGING = 'HEDGING'
                
                if self.is_section_header(doc, i):
                    doc[i]._.HEDGING = 'HEDGING'

                #if self.has_hedging_ancestor(doc[i]):
                #    print('-- Hedging ancestor detected for', doc[i])
                #    doc[i]._.HEDGING = 'HEDGING'

                #if self.has_hedging_dependent(doc[i]):
                #    print('-- Hedging dependent detected for', doc[i])
                #    doc[i]._.HEDGING = 'HEDGING'
                    
                #if self.has_historical_ancestor(doc[i]):
                #    print('-- Historical marker detected for', doc[i])
                #    doc[i]._.TIME = 'TIME'

                #if self.has_historical_dependent(doc[i]):
                #    print('-- Historical marker detected for', doc[i])
                #    doc[i]._.TIME = 'TIME'

                curr_sent = doc[i].sent
                start = i - 5
                if start < 0:
                    start = curr_sent.start
                window = doc[start:i]
                for token in window:
                    if token.sent == curr_sent:
                        if token._.NEG == 'NEG':
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
                for token in window:
                    if token.sent == curr_sent:
                        if token._.TIME == 'TIME':
                            doc[i]._.TIME = 'TIME'
                        if token._.MODALITY == 'MODALITY':
                            doc[i]._.MODALITY = 'MODALITY'
                        if token._.HEDGING == 'HEDGING':
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
        pxmlstr = parseString(xmlstr)

        if verbose:
            print(pxmlstr.toprettyxml(indent='\t'), file=sys.stderr)

        # Write to file
        #tree = ET.ElementTree(root)
        #tree.write(ehost_pout, encoding="utf-8", xml_declaration=True)
        open(ehost_pout, 'w').write(pxmlstr.toprettyxml(indent='\t'))
        print('-- Wrote EHOST file: ' + ehost_pout, file=sys.stderr)

        return root

    def process(self, path, verbose=False, write_output=True):
        # Load pronoun lemma corrector
        self.load_pronoun_lemma_corrector()

        # Load detokenizer
        self.load_detokenizer(os.path.join('resources', 'detokenization_rules.txt'))

        # Load lexical annotators
        self.load_lexicon('./resources/dsh_sequence_lex.txt', LEMMA, 'DSH', merge=True)
        #self.load_lexicon('./resources/dsh_lex_lemma.txt', LEMMA, 'DSH', merge=True)
        self.load_lexicon('./resources/time_lex.txt', None, 'TIME')
        self.load_lexicon('./resources/negation_lex.txt', LEMMA, 'NEG')
        self.load_lexicon('./resources/modality_lex.txt', LEMMA, 'MODALITY')
        self.load_lexicon('./resources/hedging_lex.txt', LEMMA, 'HEDGING')
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


if __name__ == "__main__":
    dsha = DSHAnnotator()
    #dsh_annotations = dsha.process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system/files/corpus')

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
    """text = 'she did self-imolation in the past'
    text = 'no acts of self-harm'
    text = 'she did not harm herself'
    text = 'has a history of self-abuse'
    text = 'has a history of taking multiple overdoses in the past'
    text = 'She does not report having had actual self-harm'
    text = 'She says she has never cut her arm'
    text = 'She does not report having had actual suicidal thoughts, intent or plans (and cites family reasons as being protective) as such.'
    text = 'There is no history of deliberate self-harm except for one occasion when she reports having attempted to walk into the middle of the road (but this was when she was manic in the context of grandiose thoughts)'
    text = e.g. sees sister regularly, goes to Effra day centre three days a week 


Risk history:

Harm to self: DSH & suicide attempts; poor self-care; untreated physical illness; vulnerability to exploitation
    text = 'In November 2006- Whilst in PICU at  ZZZZZ  Hospital- she described suicidal thoughts, low mood and talked about strangling babies.'"""
    text = 'she has a history of self-harm'
    text = 'she cut herself when she was 32 years old'
    text = 'Her mother has suffered from depression and attempted suicide in the past but is currently well.'
    '''text = 'She would cut herself numerous times'
    text = 'Poor coping skills - likely to show impulsive behaviour (self-harm or fire-setting) when stressed.'
    text = 'She has had five psychiatric admissions precipitated by suicidal and self-harm behaviour.'
    text = 'Self-harm'
    text = 'suicide (self harm) : with a lot of room for the very lovely self harm'''

    dsh_annotations = dsha.process(text, verbose=True, write_output=False)