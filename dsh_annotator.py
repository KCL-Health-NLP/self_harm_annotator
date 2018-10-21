# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 14:27:31 2018

@author: ABittar
"""

import os
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
                curr_sent = doc[i].sent
                window = doc[i-5:i]
                for token in window:
                    if token.sent == curr_sent:
                        if token._.NEG == 'NEG':
                            doc[i]._.NEG = 'NEG'
                        if token._.TIME == 'TIME':
                            doc[i]._.TIME = 'TIME'
                        if token._.MODALITY == 'MODALITY':
                            doc[i]._.MODALITY = 'MODALITY'

        # Hack: get attributes from window of 5 tokens after DSH mention in the same sentence
        for i in range(len(doc)):
            if doc[i]._.DSH == 'DSH':
                curr_sent = doc[i].sent
                window = doc[i:i+5]
                for token in window:
                    if token.sent == curr_sent:
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
            n += 1
            val = annotation.get('polarity', 'POSITIVE')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'polarity'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)

            # status
            n += 1
            val = annotation.get('status', 'NON-RELEVANT')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'status'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)

            # temporality
            n += 1
            val = annotation.get('temporality', 'CURRENT')
            slot_mention_node = ET.SubElement(root, 'stringSlotMention')
            slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)
            mention_slot_node = ET.SubElement(slot_mention_node, 'mentionSlot')
            mention_slot_node.attrib['id'] = 'temporality'
            string_mention_value_node = ET.SubElement(slot_mention_node, 'stringSlotMentionValue')
            string_mention_value_node.attrib['value'] = val
            has_slot_mention_node = ET.SubElement(class_mention, 'hasSlotMention')
            has_slot_mention_node.attrib['id'] = 'EHOST_Instance_' + str(n)

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
            self.write_ehost_output('test.txt', mentions, verbose=verbose)
        
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
    dsh_annotations = dsha.process('input/000000000/corpus/test_1.txt')