# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 11:18:29 2019

@author: ABittar
"""

import datetime
import os
import pandas as pd
import sys

sys.path.append('T:/Andre Bittar/workspace/utils')

from dsh_annotator import DSHAnnotator
from ehost_annotation_reader import convert_file_annotations, get_corpus_files, load_mentions_with_attributes
from pandas import Timestamp
from pprint import pprint
from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support
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


def count_true_DSH_mentions(mentions):
    mentions = convert_file_annotations(mentions)
    count = 0
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        temporality = mention.get('temporality', None)

        if polarity == 'POSITIVE' and temporality == 'CURRENT' and \
        status == 'RELEVANT':
            count += 1
            #print(mention['text'])
    
    return count
            

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


def count_dsh_mentions_per_patient_train(sys_or_gold, recalculate=False):
    """
    Load gold/train data into a DataFrame and count the number of "true" 
    DSH mentions per patient
    """
    df = pin = None

    if sys_or_gold == 'sys':
        pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient.pickle'
    else:
        pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev_patient.pickle'

    if os.path.isfile(pin) and not recalculate:
        print('-- Loading file:', pin, file=sys.stderr)
        df = pd.read_pickle(pin)
    else:
        print('-- Recalculating data...', file=sys.stderr)
        if sys_or_gold == 'sys':
            files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
        else:
            files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev_patient/files')
        xml = [f for f in files if 'xml' in f]
        txt = [f for f in files if 'xml' not in f]

        entries = []
        for (x, t) in zip(xml, txt):
            t_split = t.replace('\\', '/').split('/')
            brcid = t_split[7]
            docid = t_split[9].replace('.txt', '').split('_')[-1]
            text_content = open(t, 'r').read()
            mentions = load_mentions_with_attributes(x)
            hm = count_true_DSH_mentions(mentions)
            #hm = has_DSH_mention(mentions)
            entries.append((t, brcid, docid, text_content, hm))
        df = pd.DataFrame(entries, columns=['file', 'brcid', 'cn_doc_id', 'text_content', 'dsh'])
        df.to_pickle(pin)
        print('-- Done.', file=sys.stderr)
    
    results = {}
    for brcid in df.groupby('brcid'):
        c = 0
        for i, row in brcid[1].iterrows():
            if row.dsh > 0:
                c += row.dsh
        results[brcid[0]] = c

    return df, results


def evaluate_sys(results, sys_results):
    x_gold = []
    x_sys = []
    for brcid in results:
        x_gold.append(results.get(brcid) > 0)
        x_sys.append(sys_results.get(brcid) > 0)
    
    prf_micro = precision_recall_fscore_support(x_gold, x_sys, average='micro')
    prf_macro = precision_recall_fscore_support(x_gold, x_sys, average='macro')
    kappa = cohen_kappa_score(x_gold, x_sys)
    
    print('prf (macro):', prf_macro[:-1])
    print('prf (micro):', prf_micro[:-1])
    print('kappa      :', kappa)


def batch_process(main_dir):
    """
    Runs on actual files and outputs new XML.
    """
    dsha = DSHAnnotator(verbose=False)
    
    #main_dir = 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text'
    
    pdirs = os.listdir(main_dir)
    n = len(pdirs)
    i = 1
    
    t0 = time()
    
    for pdir in pdirs:
         pin = os.path.join(main_dir, pdir, 'corpus').replace('\\', '/')
         _ = dsha.process(pin, write_output=True)
         print(i, '/', n, pin)
         i += 1

    t1 = time()
    
    print(t1 - t0)


def process(pin):
    """
    Runs on a DataFrame that contains the text for each file.
    Outputs True for documents with relevant mention.
    Does not write new XML.
    All saved to the DataFrame.
    """
    
    now = datetime.datetime.now().strftime('%Y%m%d')
    
    dsha = DSHAnnotator(verbose=False)
    #df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    df = pd.read_pickle(pin)
    df['dsh'] = False
    n = len(df)
    
    t0 = time()
    for i, row in df.iterrows():
        docid = row.cn_doc_id
        text = row.text_content
        mentions = dsha.process_text(text, docid, write_output=False)
        df.at[i, 'dsh'] = has_DSH_mention(mentions)
        if i % 1000 == 0:
            print(i, '/', n)
        
    t1 = time()    
    
    print(t1 - t0)
    
    df.to_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed_' + now + '.pickle')
    
    return df


if __name__ == '__main__':
    print('-- Run one of the two functions...', file=sys.stderr)
    #test()
    #df_processed = process('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    #batch_process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
    