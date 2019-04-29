# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 11:18:29 2019

@author: ABittar
"""

import os
import pandas as pd
import sys

sys.path.append('T:/Andre Bittar/workspace/utils')

from dsh_annotator import DSHAnnotator
from ehost_annotation_reader import convert_file_annotations
from pandas import Timestamp
from pprint import pprint
from time import time


def has_DSH_mention(mentions):
    mentions = convert_file_annotations(mentions)
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        temporality = mention.get('temporality', None)
        
        # doing these checks separately might save a tiny bit of time
        if status != 'RELEVANT':
            continue

        # if status is relevant the polarity *should* always be positive, but check just in case
        if polarity != 'POSITIVE':
            continue

        if temporality == 'CURRENT':
            return True

    return False


def output_for_batch_processing(target_dir):
    # use target_dir: 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/'
    df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    df['date'] = df.viewdate.map(Timestamp.date)

    for i, row in df.iterrows():
        brcid = str(int(row.brcid))
        cndocid = str(row.cn_doc_id)
        text = str(row.text_content)
        docdate = str(row.date)
        if not os.path.isdir(target_dir + brcid):
            os.makedirs(target_dir + brcid)
            os.mkdir(target_dir + brcid + '/config')
            os.mkdir(target_dir + brcid + '/corpus')
            os.mkdir(target_dir + brcid + '/saved')
        pout = target_dir + brcid + '/corpus/' + docdate + '_' + cndocid + '_' + str(i) + '.txt'
        with open(pout, 'w', encoding='utf-8') as fout:
            print(text, file=fout)
        fout.close()
        if i % 1000 == 0:
            print(i, '/', len(df))
    
    print('Files saved to target directory:', target_dir)


def test():
    dsha = DSHAnnotator()
    
    texts = ['She has self-harmed in the past.', 'No evidence of cutting herself, but does have DSH. She is self-harming.']    
    
    n = 1
    global_mentions = {}
    
    for text in texts:
        text_id = 'text_' + str(n).zfill(5)
        n += 1
        mentions = dsha.process_text(text, text_id, verbose=False, write_output=False)
        print('HAS DSH:', has_DSH_mention(mentions))
        global_mentions.update(mentions)
    
    pprint(global_mentions)


def batch_process():
    dsha = DSHAnnotator()
    
    main_dir = 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text'
    
    pdirs = os.listdir(main_dir)
    n = len(pdirs)
    i = 1
    
    t0 = time()
    
    for pdir in pdirs:
         pin = os.path.join(main_dir, pdir, 'corpus')
         _ = dsha.process(pin, verbose=False, write_output=True)
         print(i, '/', n, pin)
         i += 1

    t1 = time()
    
    print(t1 - t0)
        

def process():
    dsha = DSHAnnotator()
    df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    df['dsh'] = False
    n = len(df)
    
    t0 = time()
    for i, row in df.iterrows():
        docid = row.cn_doc_id
        text = row.text_content
        mentions = dsha.process_text(text, docid, verbose=False, write_output=False)
        df.at[i, 'dsh'] = has_DSH_mention(mentions)
        if i % 1000 == 0:
            print(i, '/', n)
        
    t1 = time()    
    
    print(t1 - t0)
    
    return df


if __name__ == '__main__':
    #test()
    #df_processed = process()
    batch_process()