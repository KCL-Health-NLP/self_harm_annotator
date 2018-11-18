# -*- coding: utf-8 -*-
"""
Created on Mon Aug  6 11:26:54 2018

@author: ABittar
"""

import os
import pickle
import spacy
import sys

sys.path.append('T:/Andre Bittar/workspace/utils')

from ehost_annotation_reader import batch_process_directory
from spacy.tokens import Token

DSH_ATTRIBUTES = ['mclass', 'polarity', 'status', 'temporality']
DEFAULT_ATTR_VALUE = False


def transfer_annotations_to_span(annotation, span):
    for token in span:
        for attr in DSH_ATTRIBUTES:
            # use  mmclass to avoid syntax error wiith class when checking
            # during DSH sentence collection
            if attr == 'mclass':
                token._.set(attr, annotation.get('class', DEFAULT_ATTR_VALUE))
            else:
                token._.set(attr, annotation.get(attr, DEFAULT_ATTR_VALUE))
    return span


def set_custom_attributes(attributes):
    for attr in attributes:
        Token.set_extension(attr, default=DEFAULT_ATTR_VALUE, force=True)


def set_token_attributes(token):
    annotation = {}
    
    # Standard attributes
    #annotation['_'] = token._
    annotation['cluster'] = token.cluster
    #annotation['dep'] = token.dep
    annotation['dep_'] = token.dep_
    #annotation['doc'] = token.doc
    annotation['ent_id'] = token.ent_id
    annotation['ent_id_'] = token.ent_id_
    annotation['ent_iob'] = token.ent_iob
    annotation['ent_iob_'] = token.ent_iob_
    annotation['ent_type'] = token.ent_type
    annotation['ent_type_'] = token.ent_type_
    annotation['head'] = token.head.i
    annotation['i'] = token.i
    annotation['idx'] = token.idx
    annotation['is_alpha'] = token.is_alpha
    annotation['is_ascii'] = token.is_ascii
    annotation['is_bracket'] = token.is_bracket
    annotation['is_currency'] = token.is_currency
    annotation['is_digit'] = token.is_digit
    annotation['is_left_punct'] = token.is_left_punct
    annotation['is_lower'] = token.is_lower
    annotation['is_oov'] = token.is_oov
    annotation['is_punct'] = token.is_punct
    annotation['is_quote'] = token.is_quote
    annotation['is_right_punct'] = token.is_right_punct
    annotation['is_space'] = token.is_space
    annotation['is_stop'] = token.is_stop
    annotation['is_title'] = token.is_title
    annotation['is_upper'] = token.is_upper
    #annotation['lang'] = token.lang
    annotation['lang_'] = token.lang_
    #annotation['left_edge'] = token.left_edge
    #annotation['lemma'] = token.lemma
    annotation['lemma_'] = token.lemma_
    annotation['lex_id'] = token.lex_id
    annotation['like_email'] = token.like_email
    annotation['like_num'] = token.like_num
    annotation['like_url'] = token.like_url
    #annotation['lower'] = token.lower
    annotation['lower_'] = token.lower_
    #annotation['norm'] = token.norm
    annotation['norm_'] = token.norm_
    #annotation['orth'] = token.orth
    annotation['orth_'] = token.orth_
    annotation['pos'] = token.pos
    annotation['pos_'] = token.pos_
    #annotation['prefix'] = token.prefix
    annotation['prefix_'] = token.prefix_
    annotation['prob'] = token.prob
    annotation['rank'] = token.rank
    #annotation['right_edge'] = token.right_edge
    annotation['sentiment'] = token.sentiment
    #annotation['shape'] = token.shape
    annotation['shape_'] = token.shape_
    #annotation['suffix'] = token.suffix
    annotation['suffix_'] = token.suffix_
    #annotation['tag'] = token.tag
    annotation['tag_'] = token.tag_
    annotation['text'] = token.text
    annotation['text_with_ws'] = token.text_with_ws
    #annotation['vocab'] = token.vocab
    annotation['whitespace_'] = token.whitespace_
    
    # Custom attributes
    for attr in DSH_ATTRIBUTES:
        val = token._.get(attr)
        annotation[attr] = val
    
    return annotation

        
def collect_annotations(doc, pout, dsh_sentences_only=False):
    annotations = []
    
    base_sents = []
    
    print('-- Collecting base sentences', file=sys.stderr)
    for token in doc:
        if dsh_sentences_only:
            if token._.mclass == 'SELF-HARM':
                base_sents.append(token.sent)
        else:
            base_sents.append(token.sent)
    
    print('-- Collecting token annotations', file=sys.stderr)
    annotated_sentences = []

    for sent in base_sents:
        for token in sent:
            annotation = set_token_attributes(token)
            annotations.append(annotation)

        annotated_sentences.append(annotations)
        #from pprint import pprint
        #pprint(annotated_sentences)

    print('-- Saving spaCy token annotations:', pout)
    pickle.dump(annotated_sentences, open(pout, 'wb'))
    
    return annotations
    

def transfer_annotations():
    set_custom_attributes(DSH_ATTRIBUTES)

    nlp = spacy.load('en')
    kas = batch_process_directory('T:\\Andre Bittar\\Projects\\KA_Self-harm\\Adjudication\\gold')

    fout = open('T:/Andre Bittar/workspace/dsh_annotator/output/report_2.txt', 'w')
    for f in list(kas.keys()):
        t = f.replace('.knowtator.xml', '').replace('saved', 'corpus')
        text = open(t, 'r').read()
        doc = nlp(text)

        tokens = {}
        for token in doc:
            tokens[token.idx] = token
        
        spans = []
       
        for eid in kas[f]:
            annotation = kas[f][eid]
            start = int(annotation['start'])
            end = int(annotation['end'])
            text = annotation['text']

            start_token = tokens.get(start, tokens.get(start - 1, tokens.get(start + 1, None)))
            end_token = tokens.get(end, tokens.get(end + 1, None))

            if start_token is not None:

                if end_token is not None:
                    span = doc[start_token.i:end_token.i]
                    print(start_token.idx, end_token.idx, span)
                    print(start_token.idx, end_token.idx, span, file=fout)
                else:
                    span = doc[start_token.i:start_token.i + 1]
                    print(start_token.idx, start_token.idx, span)
                    print(start_token.idx, start_token.idx, span, file=fout)

                span = transfer_annotations_to_span(annotation, span)
                spans.append(span)

            else:
                print('-- Error on token for annotation ' + eid + ' (' + f + '):', start, end, text, annotation, file=fout)
            print('---', file=fout)

        #patient_dir = os.path.basename(os.path.abspath(os.path.join(os.path.dirname(f), os.pardir)))
        #saved_dir = os.path.basename(os.path.dirname(f))

        # merge all span into single tokens
        for span in spans:
            span.merge()

        """ Print to see if this has worked - yep.
        for token in doc:
            for attr in DSH_ATTRIBUTES:
                val = token._.get(attr)
                if val:
                    print(token, attr, val)"""

        pfout = os.path.join('T:/Andre Bittar/workspace/dsh_annotator/data', os.path.basename(f) + '_spacy.pickle')
        collect_annotations(doc, pfout)

        #pfout = os.path.join('T:/Andre Bittar/workspace/ka_dsh/data', os.path.basename(f) + '.spacy')
        #print('-- Saving enriched spaCy document:', pfout)
        #doc.to_disk(pfout)

    fout.close()
    
    return nlp


def extract_features(mention):
    pass


def process(pin):
    tokens = pickle.load(open(pin, 'rb'))
    
    for token in tokens:
        _class = token.get('class', None)
        if _class == 'SELF-HARM':
            from pprint import pprint
            print(token['text'], end='\n')
            pprint(token)
            print()