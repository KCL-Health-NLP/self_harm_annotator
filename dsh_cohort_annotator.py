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


def has_DSH_mention(mentions, check_temporality):
    mentions = convert_file_annotations(mentions)
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        temporality = mention.get('temporality', None)
        
        if not check_temporality:
            if status == 'RELEVANT' and polarity == 'POSITIVE':
                return True        
        else:
            # doing these checks separately might save a tiny bit of time
            if status != 'RELEVANT':
                continue

            # if status is relevant the polarity *should* always be positive, but check just in case
            if polarity != 'POSITIVE':
                continue

            if temporality == 'CURRENT':
                return True
            
    return False


def count_true_DSH_mentions(mentions, check_temporality):
    mentions = convert_file_annotations(mentions)
    count = 0
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)

        if not check_temporality:
            if polarity == 'POSITIVE' and status == 'RELEVANT':
                count += 1
                #print(mention['text'])
        else:
            temporality = mention.get('temporality', None)

            if polarity == 'POSITIVE' and temporality == 'CURRENT' and \
            status == 'RELEVANT':
                count += 1
                #print(mention['text'])
    
    return count


def output_for_batch_processing(path, target_dir):
    # use target_dir: 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/'
    #df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    # 'T:/Andre Bittar/Projects/CC_Eating_Disorder/balanced_sample_700.pickle'
    df = pd.read_pickle(path)
    df.rename(columns={'viewdate': 'date'}, inplace=True)
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


def test(check_temporality):
    dsha = DSHAnnotator()
    
    texts = ['Psychiatric history: she reports having self-harmed.', 'She has self-harmed in the past.', 'No evidence of cutting herself, but does have DSH. She is self-harming.']    
    
    n = 1
    global_mentions = {}
    
    for text in texts:
        text_id = 'text_' + str(n).zfill(5)
        n += 1
        mentions = dsha.process_text(text, text_id, verbose=False, write_output=False)
        print('HAS DSH:', has_DSH_mention(mentions, check_temporality=check_temporality))
        global_mentions.update(mentions)
    
    pprint(global_mentions)


def count_dsh_mentions_per_patient_train(sys_or_gold, recalculate=False):
    """
    Load gold/train data into a DataFrame and count the number of "true" 
    DSH mentions per patient
    """
    df = pin = None

    if sys_or_gold == 'sys':
        #pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient.pickle'
        pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_test_patient.pickle'
    elif sys_or_gold == 'gold':
        #pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev_patient.pickle'
        pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test_patient.pickle'
    elif sys_or_gold == 'cohort':
        pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/text'
    else:
        raise ValueError('-- Incorrect argument:', sys_or_gold, 'use "sys" or "gold".')

    if os.path.isfile(pin) and not recalculate:
        print('-- Loading file:', pin, file=sys.stderr)
        df = pd.read_pickle(pin)
    else:
        print('-- Recalculating data...', file=sys.stderr)
        if sys_or_gold == 'sys':
            #files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
            files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_test_patient/files')
        elif sys_or_gold == 'gold':
            #files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev_patient/files')
            files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test_patient/files')
        else:
            files = get_corpus_files(pin)
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
        
        if sys_or_gold != 'cohort':
            print('-- Saved file:', pin)
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


def count_cohort_mentions():
    #files = get_corpus_files('Z:/Andre Bittar/Projects/KA_Self-harm/data/text')
    files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test_patient')
    xml = [f for f in files if 'xml' in f]
    txt = [f for f in files if 'xml' not in f]
    entries = []
    for (x, t) in zip(xml, txt):
        t_split = t.replace('\\', '/').split('/')
        brcid = t_split[6]
        docid = t_split[8].replace('.txt', '').split('_')[-1]
        text_content = open(t, 'r', encoding='latin-1').read()
        mentions = load_mentions_with_attributes(x)
        hm = count_true_DSH_mentions(mentions, check_temporality=True)
        #hm = has_DSH_mention(mentions)
        entries.append((t, brcid, docid, text_content, hm))

    df = pd.DataFrame(entries, columns=['file', 'brcid', 'cn_doc_id', 'text_content', 'dsh'])
    df.to_pickle('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test_patient.pickle')
    print('-- Done.', file=sys.stderr)
    
    results = {}
    for brcid in df.groupby('brcid'):
        c = 0
        for i, row in brcid[1].iterrows():
            if row.dsh > 0:
                c += row.dsh
        results[brcid[0]] = c

    return df, results


def count_flagged_patients(df_processed, key, check_counts=True):
    """
    key: dsh_YYYYMMDD_tmp or dsh_YYYYMMDD_notmp
    """
    n = 0
    t = 0
    for g in df_processed.groupby('brcid'):
        for i, row in g[1].iterrows():
            if check_counts:
                if row[key] > 0:
                    n += 1
                    break
            elif row[key] == True:
                n += 1
                break
        t += 1
    
    print('Flagged patients:', n)
    print('Total patients  :', t)
    print('% flagged       :', n / t * 100)


def evaluate_sys(results, sys_results):
    """
    
    """
    x_gold = []
    x_sys = []
    
    for brcid in results:
        x_gold.append(results.get(brcid) > 0)
        x_sys.append(sys_results.get(brcid) > 0)
 
    print(x_gold)
    print(x_sys)
    
    n = len(x_gold)
    n_gold = len([x for x in x_gold if x == True])
    n_sys = len([x for x in x_sys if x == True])
    
    report_string = 'Patient-level performance metrics\n'
    report_string += '---------------------------------\n'
    report_string += 'Gold patients:' + str(n_gold) + ' (' + str(n_gold / n * 100) + '%)\n'
    report_string += 'Sys patients :' + str(n_sys) + ' (' + str(n_sys / n * 100) + '%)\n'
    scores = {}
    scores['macro'] = precision_recall_fscore_support(x_gold, x_sys, average='macro')
    scores['micro'] = precision_recall_fscore_support(x_gold, x_sys, average='micro')
            
    for score in scores:
        report_string += 'precision (' + score + '): ' + str(scores[score][0]) + '\n'
        report_string += 'recall    (' + score + '): ' + str(scores[score][1]) + '\n'
        report_string += 'f-score   (' + score + '): ' + str(scores[score][2]) + '\n'

    k = cohen_kappa_score(x_gold, x_sys)
    report_string += 'kappa            : ' + str(k) + '\n'

    print(report_string)


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


def process(pin, check_counts=True, check_temporality=True):
    """
    Runs on a DataFrame that contains the text for each file.
    Outputs True for documents with relevant mention.
    Does not write new XML.
    All saved to the DataFrame.
    """
    
    now = datetime.datetime.now().strftime('%Y%m%d')

    if check_temporality:
        now += '_tmp'
    else:
        now += '_notmp'
    
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
        if check_counts:
            df.at[i, 'dsh_' + now] = count_true_DSH_mentions(mentions, check_temporality=check_temporality)
        else:
            df.at[i, 'dsh_' + now] = has_DSH_mention(mentions, check_temporality=check_temporality)
        if i % 1000 == 0:
            print(i, '/', n)
        if i % 10000 == 0:
            print('-- Creating backup:', pin)
            df.to_pickle(pin)

    t1 = time()
    
    print(t1 - t0)
    
    print('-- Wrote file:', pin)
    df.to_pickle(pin)
    
    return df


if __name__ == '__main__':
    print('-- Check has_DSH_mention() internal settings...', file=sys.stderr)
    print('-- Check process() internal settings...', file=sys.stderr)
    print('-- Run one of the two functions...', file=sys.stderr)
    #test(check_temporality=True)
    #df_processed = process('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle', check_counts=True, check_temporality=True)
    #batch_process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
    