# -*- coding: utf-8 -*-
"""
    This is a utility script to annotate specific cohorts, e.g. Karyn Ayre's
    perinatal DSH cohort, Charlotte Cliffe's eating disorder cohort.
    Execution examples are provided in comments in the main() method.
"""

import datetime
import os
import pandas as pd
import sys

sys.path.append('T:/Andre Bittar/workspace/utils')

from db_connection import fetch_dataframe, db_name, server_name
from dsh_annotator import DSHAnnotator
from ehost_annotation_reader import convert_file_annotations, get_corpus_files, load_mentions_with_attributes
from pandas import Timestamp
from pprint import pprint
from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support
from time import time

__author__ = "André Bittar"
__copyright__ = "Copyright 2020, André Bittar"
__credits__ = ["André Bittar"]
__license__ = "GPL"
__email__ = "andre.bittar@kcl.ac.uk"


def has_DSH_mention(mentions, check_temporality):
    """
    Check if any of the mentions are positive depending on the predefined study
    criteria. e.g. for Karyn's project these are polarty=POSITIVE, 
    status=RELEVANT, temporality=CURRENT.
    
    Arguments:
        - mentions: dict; a dictionary of annotations.

    Return: bool; True if a positive mention is found, else False.
    """
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
    """
    Count the number of positive mentions.
    This is for heuristics that look only at the number of mentions.
    """
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

def get_true_DSH_mentions(mentions, check_temporality):
    """
    Get the text of all positive mentions.
    This is for heuristics that compare the text of mentions.
    """
    mentions = convert_file_annotations(mentions)
    texts = []
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        text = mention.get('text', None)

        if not check_temporality:
            if polarity == 'POSITIVE' and status == 'RELEVANT':
                if text is not None:
                    texts.append(text)
        else:
            temporality = mention.get('temporality', None)

            if polarity == 'POSITIVE' and temporality == 'CURRENT' and \
            status == 'RELEVANT':
                if text is not None:
                    texts.append(text)
                    #print(mention['text'])
    
    return '|'.join(texts)

def output_for_batch_processing(path, target_dir):
    """
    From a DataFrame containing all text data extracted from CRIS, create an
    eHOST directory structure ready for files to be manually annotated.
    """
    # use target_dir: 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/'
    #df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    # 'T:/Andre Bittar/Projects/CC_Eating_Disorder/balanced_sample_700.pickle'
    df = pd.read_pickle(path)
    df.rename(columns={'viewdate': 'date'}, inplace=True)
    df['date'] = df.date.map(Timestamp.date)

    for i, row in df.iterrows():
        brcid = str(int(row.brcid))
        cndocid = str(row.cn_doc_id)
        text = str(row.text_content)
        docdate = str(row.date)
        if not os.path.isdir(target_dir + '/' + brcid):
            os.makedirs(target_dir + '/' + brcid)
            os.mkdir(target_dir + '/' + brcid + '/config')
            os.mkdir(target_dir + '/' + brcid + '/corpus')
            os.mkdir(target_dir + '/' + brcid + '/saved')
        pout = target_dir + '/' + brcid + '/corpus/' + docdate + '_' + cndocid + '_' + str(i) + '.txt'
        with open(pout, 'w', encoding='utf-8') as fout:
            print(text, file=fout)
        fout.close()
        if i % 1000 == 0:
            print(i, '/', len(df))
    
    print('Files saved to target directory:', target_dir)


def test(check_temporality):
    """
    Run some test examples.
    """
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
    Load gold/train data into a DataFrame and count the number of "true" (positive)
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
    """
    Count all positive DSH mentions in the manually annotated cohort documents
    (in eHOST) format.
    """
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


def count_flagged_patients(df_processed, key, heuristic='base'):
    """
    Count all patients flagged with a postive mention.
    key: dsh_YYYYMMDD_tmp or dsh_YYYYMMDD_notmp
    """    
    n = 0
    t = 0
    for g in df_processed.groupby('brcid'):
        true_texts = []
        for i, row in g[1].iterrows():
            if heuristic == 'base':
                if row[key] > 0:
                    n += 1
                    break
            elif heuristic == '2m':
                if row[key] > 1:
                    n += 1
                    break
            elif heuristic in ['2m_diff', '2m_diff_strict']:
                s = row[key].split('|')
                if '' in s:
                    s.remove('')
                true_texts += s
            elif isinstance(row[key], bool) and row[key]:
                    n += 1
                    break
        if heuristic in ['2m_diff', '2m_diff_strict']:
            texts_unique = set(true_texts)
            if heuristic == '2m_diff':
                if len(true_texts) > 1 and len(texts_unique) > 1:
                    n += 1
            elif heuristic == '2m_diff_strict':
                if len(true_texts) > 1 and len(true_texts) == len(texts_unique):
                    n += 1
        t += 1
    
    print('Flagged patients:', n)
    print('Total patients  :', t)
    print('% flagged       :', n / t * 100)


def evaluate_sys(results, sys_results):
    """
    Perform evaluation of the app in comparison with the gold standard manual
    annotations.
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
    Run the dsh_annotator on text files and output new XML.
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


def process_CC_EE():
    """
    Run entire process from CRIS query to flagging of patients.
    This will get latest data from CRIS.
    """
    # load and store new data for Attachement
    print('-- Fetching Attachment data...', end='')
    query_att = open('T:/Andre Bittar/Projects/CC_Eating_Disorder/CC_Eating_Disorder_get_texts_Attachment_query.sql', 'r').read()
    df_att = fetch_dataframe(server_name, db_name, query_att)
    df_att.rename(columns={'BrcId': 'brcid', 'CN_Doc_ID': 'cn_doc_id', 'ViewDate': 'viewdate', 'Attachment_Text': 'text_content'}, inplace=True)
    print('Done.')
    
    # load and store new data for Event
    print('-- Fetching Event data...', end='')
    query_evt = open('T:/Andre Bittar/Projects/CC_Eating_Disorder/CC_Eating_disorder_get_texts_Event_query.sql', 'r').read()
    df_evt = fetch_dataframe(server_name, db_name, query_evt)
    df_evt.rename(columns={'BrcId': 'brcid', 'CN_Doc_ID': 'cn_doc_id', 'ViewDate': 'viewdate', 'Comments': 'text_content'}, inplace=True)
    print('Done.')
    
    df_new = pd.concat([df_att, df_evt])
    df_new.reset_index(drop=True, inplace=True)
    
    del df_att
    del df_evt
    
    now = datetime.datetime.now().strftime('%Y%m%d')
    new_p = 'T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_DSH_new_' + now + '.pickle'
    df_new.to_pickle(new_p)
    
    print('-- Processing...')
    df_new = process(new_p, check_counts=False, check_temporality=False)
    df_new.to_pickle(new_p)
    
    # output an Excel spreadsheet with flagged patients
    df_flags = pd.DataFrame(columns=['brcid', 'dsh'])
    for g in df_new.groupby('brcid'):
        brcid = g[0]
        flag = False
        for i, row in g[1].iterrows():
            if row['dsh_' + now + '_notmp'] == True:
                tmp = pd.DataFrame({'brcid': [brcid], 'dsh': [True]})
                df_flags = pd.concat([df_flags, tmp])
                flag = True
                break
        if flag == False:
            tmp = pd.DataFrame({'brcid': [brcid], 'dsh': [False]})
            df_flags = pd.concat([df_flags, tmp])
    
    df_flags.reset_index(drop=True, inplace=True)
    df_flags.sort_values(by='brcid', inplace=True)
    df_flags.to_excel('T:/Andre Bittar/Projects/CC_Eating_Disorder/flagged_patients_full_cohort_' + now + '.xlsx')
    
    return df_flags


def process_CC_EE_update():
    """
    Run process on new data only and merge with old data.
    """
    # Load original data
    print('-- Loading original data...', end='')
    df = pd.read_pickle('T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_DSH.pickle')
    print('Done.')
    
    # load and store new data for Attachement
    print('-- Fetching Attachment data...', end='')
    query_att = open('T:/Andre Bittar/Projects/CC_Eating_Disorder/CC_Eating_Disorder_get_texts_Attachment_query.sql', 'r').read()
    df_att = fetch_dataframe(server_name, db_name, query_att)
    df_att.rename(columns={'BrcId': 'brcid', 'CN_Doc_ID': 'cn_doc_id', 'ViewDate': 'viewdate', 'Attachment_Text': 'text_content'}, inplace=True)
    df_att = df_att.loc[~df_att.cn_doc_id.isin(df.cn_doc_id)]
    print('Done.')
    
    # load and store new data for Event
    print('-- Fetching Event data...', end='')
    query_evt = open('T:/Andre Bittar/Projects/CC_Eating_Disorder/CC_Eating_disorder_get_texts_Event_query.sql', 'r').read()
    df_evt = fetch_dataframe(server_name, db_name, query_evt)
    df_evt.rename(columns={'BrcId': 'brcid', 'CN_Doc_ID': 'cn_doc_id', 'ViewDate': 'viewdate', 'Comments': 'text_content'}, inplace=True)
    df_evt = df_evt.loc[~df_evt.cn_doc_id.isin(df.cn_doc_id)]
    print('Done.')
    
    df_new = pd.concat([df_att, df_evt])
    df_new.reset_index(drop=True, inplace=True)
    
    del df_att
    del df_evt
    
    now = datetime.datetime.now().strftime('%Y%m%d')
    new_p = 'T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_DSH_new_' + now + '.pickle'
    df_new.to_pickle(new_p)
    
    print('-- Processing...')
    df_new = process(new_p, check_counts=False, check_temporality=False)
    df_new.to_pickle(new_p)
    
    # now merge the latest column from df with the new one from df_new
    latest_key = [t for t in sorted(list(df.columns)) if '_notmp' in t][-1]
    df_tmp = df[['brcid', 'cn_doc_id', 'viewdate', 'text_content', 'age', latest_key]]
    df_tmp.rename(columns={latest_key: 'dsh_' + now + '_notmp'}, inplace=True)
    
    # TODO do the merge
    
    # output an Excel spreadsheet with flagged patients
    df_flags = pd.DataFrame(columns=['brcid', 'dsh'])
    for g in df_tmp.groupby('brcid'):
        brcid = g[0]
        flag = False
        for i, row in g[1].iterrows():
            if row['dsh_20200128_notmp'] == True:
                tmp = pd.DataFrame({'brcid': [brcid], 'dsh': [True]})
                df_flags = pd.concat([df_flags, tmp])
                flag = True
                break
        if flag == False:
            tmp = pd.DataFrame({'brcid': [brcid], 'dsh': [False]})
            df_flags = pd.concat([df_flags, tmp])
    
    df_flags.to_excel('T:/Andre Bittar/Projects/CC_Eating_Disorder/flagged_patients_updated_cohort' + now + '.xlsx')
    
    return df_flags


def process(pin, check_counts=True, check_temporality=True, heuristic='base'):
    """
    Run dsh_annotator on a DataFrame that contains the text for each file.
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
    #df['dsh'] = False
    n = len(df)
    
    t0 = time()
    for i, row in df.iterrows():
        docid = row.cn_doc_id
        text = row.text_content
        mentions = dsha.process_text(text, docid, write_output=False)
        if check_counts:
            if heuristic in ['base', '2m']:
                df.at[i, 'dsh_' + now] = count_true_DSH_mentions(mentions, check_temporality=check_temporality)
            else:
                text = get_true_DSH_mentions(mentions, check_temporality=check_temporality)
                #print(i, docid, text)
                df.at[i, 'dsh_' + now] = text
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
    #df_processed = process('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle', check_counts=True, check_temporality=True, heuristic='2m_diff')
    #batch_process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
    