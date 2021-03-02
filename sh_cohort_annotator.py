# -*- coding: utf-8 -*-
"""
    This is a utility script to annotate specific cohorts, e.g. Karyn Ayre's
    perinatal SH cohort, Charlotte Cliffe's eating disorder cohort.
    Execution examples are provided in comments in the main() method.
"""

import os
import pandas as pd
import sys

sys.path.append('T:/Andre Bittar/workspace/utils')

from datetime import date
from db_connection import fetch_dataframe, db_name, server_name
from sh_annotator import SHAnnotator
from ehost_annotation_reader import convert_file_annotations, get_corpus_files, load_mentions_with_attributes
from evaluate_patient_level import get_brcid_mapping
from pandas import Timestamp
from pprint import pprint
from shutil import copy, move
from sklearn.metrics import cohen_kappa_score, precision_recall_fscore_support, classification_report
from time import time

__author__ = "André Bittar"
__copyright__ = "Copyright 2020, André Bittar"
__credits__ = ["André Bittar"]
__license__ = "GPL"
__email__ = "andre.bittar@kcl.ac.uk"


HEURISTICS = ['1m_doc', '2m_doc', '1m_patient', '2m_patient', '2m_diff_doc', '2m_diff_patient', '2m_diff_strict_doc', '2m_diff_strict_patient']


def has_SH_mention(mentions, check_temporality):
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


def count_true_SH_mentions(mentions, check_temporality):
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


def get_true_SH_mentions(mentions, check_temporality):
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
        text += '#' + mention.get('sh_type', 'SELF-HARM')

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


def output_for_batch_processing(source, target_dir, config_file=None):
    """
    From a DataFrame containing all text data extracted from CRIS, create an
    eHOST directory structure ready for files to be manually annotated.
    """
    # use target_dir: 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text/'
    #df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    # 'T:/Andre Bittar/Projects/CC_Eating_Disorder/balanced_sample_700.pickle'
    df = None
    if isinstance(source, pd.DataFrame):
        df = source
    elif isinstance(source, str):
        df = pd.read_pickle(source)
        df.rename(columns={'viewdate': 'date'}, inplace=True)
        df['date'] = df.date.map(Timestamp.date)
    else:
        raise TypeError('Invalid argument: source must be a DataFrame or a path string.')

    for i, row in df.iterrows():
        brcid = str(int(row.brcid))
        cndocid = str(row.cn_doc_id)
        text = str(row.text_content)
        #docdate = str(row.date)
        if not os.path.isdir(target_dir + '/' + brcid):
            os.makedirs(target_dir + '/' + brcid)
            os.mkdir(target_dir + '/' + brcid + '/config')
            os.mkdir(target_dir + '/' + brcid + '/corpus')
            os.mkdir(target_dir + '/' + brcid + '/saved')
        #pout = target_dir + '/' + brcid + '/corpus/' + docdate + '_' + cndocid + '_' + str(i) + '.txt'
        pout = target_dir + '/' + brcid + '/corpus/' + cndocid + '_' + str(i) + '.txt'
        with open(pout, 'w', encoding='utf-8') as fout:
            print(text, file=fout)
        fout.close()
        if config_file is not None:
            copy(config_file, target_dir + '/' + brcid + '/config')
        if i % 1000 == 0:
            print(i, '/', len(df))
    
    print('Files saved to target directory:', target_dir)


def test(check_temporality):
    """
    Run some test examples.
    """
    sha = SHAnnotator()
    
    texts = ['Psychiatric history: she reports having self-harmed.', 'She has self-harmed in the past.', 'No evidence of cutting herself, but does have SH. She is self-harming.']    
    
    n = 1
    global_mentions = {}
    
    for text in texts:
        text_id = 'text_' + str(n).zfill(5)
        n += 1
        mentions = sha.process_text(text, text_id, verbose=False, write_output=False)
        print('HAS SH:', has_SH_mention(mentions, check_temporality=check_temporality))
        global_mentions.update(mentions)
    
    pprint(global_mentions)


def count_sh_mentions_per_patient_train(sys_or_gold, recalculate=False):
    """
    Load gold/train data into a DataFrame and count the number of "true" (positive)
    SH mentions per patient
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
            hm = count_true_SH_mentions(mentions)
            #hm = has_SH_mention(mentions)
            entries.append((t, brcid, docid, text_content, hm))

        df = pd.DataFrame(entries, columns=['file', 'brcid', 'cn_doc_id', 'text_content', 'sh'])
        
        if sys_or_gold != 'cohort':
            print('-- Saved file:', pin)
            df.to_pickle(pin)
        
        print('-- Done.', file=sys.stderr)
    
    results = {}
    for brcid in df.groupby('brcid'):
        c = 0
        for i, row in brcid[1].iterrows():
            if row.sh > 0:
                c += row.sh
        results[brcid[0]] = c

    return df, results


def count_cohort_mentions():
    """
    Count all positive SH mentions in the manually annotated cohort documents
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
        hm = count_true_SH_mentions(mentions, check_temporality=True)
        #hm = has_SH_mention(mentions)
        entries.append((t, brcid, docid, text_content, hm))

    df = pd.DataFrame(entries, columns=['file', 'brcid', 'cn_doc_id', 'text_content', 'sh'])
    #df.to_pickle('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/test_patient.pickle')
    print('-- Done.', file=sys.stderr)
    
    results = {}
    for brcid in df.groupby('brcid'):
        c = 0
        for i, row in brcid[1].iterrows():
            if row.sh > 0:
                c += row.sh
        results[brcid[0]] = c

    return df, results


def evaluate_sys(results, sys_results):
    """
    DEPRECATED - only deal with base heuristic
    
    Perform evaluation of the app in comparison with the gold standard manual
    annotations.
    results; dict: gold standard results containing number of mentions per BRCID
    sys_results, dict: system results containing number of mentions per BRCID
    
    NB: use one of the counting methods to create the dictionaries
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
    Run the sh_annotator on text files and output new XML.
    """
    sha = SHAnnotator(verbose=False)
    
    #main_dir = 'Z:/Andre Bittar/Projects/KA_Self-harm/data/text'
    
    pdirs = os.listdir(main_dir)
    n = len(pdirs)
    i = 1
    
    t0 = time()
    
    for pdir in pdirs:
         pin = os.path.join(main_dir, pdir, 'corpus').replace('\\', '/')
         _ = sha.process(pin, write_output=True)
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
    
    now = str(date.today()).replace('-', '')
    new_p = 'T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_SH_new_' + now + '.pickle'
    df_new.to_pickle(new_p)
    
    print('-- Processing...')
    df_new = process(new_p, check_counts=False, check_temporality=False)
    df_new.to_pickle(new_p)
    
    # output an Excel spreasheet with flagged patients
    df_flags = pd.DataFrame(columns=['brcid', 'sh'])
    for g in df_new.groupby('brcid'):
        brcid = g[0]
        flag = False
        for i, row in g[1].iterrows():
            if row['sh_' + now + '_notmp'] == True:
                tmp = pd.DataFrame({'brcid': [brcid], 'sh': [True]})
                df_flags = pd.concat([df_flags, tmp])
                flag = True
                break
        if flag == False:
            tmp = pd.DataFrame({'brcid': [brcid], 'sh': [False]})
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
    df = pd.read_pickle('T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_SH.pickle')
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
    
    now = str(date.today()).replace('-', '')
    new_p = 'T:/Andre Bittar/Projects/CC_Eating_Disorder/all_text_processed_SH_new_' + now + '.pickle'
    df_new.to_pickle(new_p)
    
    print('-- Processing...')
    df_new = process(new_p, check_counts=False, check_temporality=False)
    df_new.to_pickle(new_p)
    
    # now merge the latest column from df with the new one from df_new
    latest_key = [t for t in sorted(list(df.columns)) if '_notmp' in t][-1]
    df_tmp = df[['brcid', 'cn_doc_id', 'viewdate', 'text_content', 'age', latest_key]]
    df_tmp.rename(columns={latest_key: 'sh_' + now + '_notmp'}, inplace=True)
    
    # TODO do the merge
    
    # output an Excel spreasheet with flagged patients
    df_flags = pd.DataFrame(columns=['brcid', 'sh'])
    for g in df_tmp.groupby('brcid'):
        brcid = g[0]
        flag = False
        for i, row in g[1].iterrows():
            if row['sh_20200128_notmp'] == True:
                tmp = pd.DataFrame({'brcid': [brcid], 'sh': [True]})
                df_flags = pd.concat([df_flags, tmp])
                flag = True
                break
        if flag == False:
            tmp = pd.DataFrame({'brcid': [brcid], 'sh': [False]})
            df_flags = pd.concat([df_flags, tmp])
    
    df_flags.to_excel('T:/Andre Bittar/Projects/CC_Eating_Disorder/flagged_patients_updated_cohort' + now + '.xlsx')
    
    return df_flags


def load_ehost_to_dataframe(pin, key, attribute='text', df=None, pin_ref=None):
    """
    Load annotations (mention text) from a directory containing eHOST annotations
    into a Pandas DataFrame
    pin, str: the path to the annotated files
    key, str: a key to name the column in which to store SH results
    df, DataFrame: an existing DataFrame to add further results to
    map_brcids, bool: get a mapping from the gold corpus (True) or from the annotated file names (False)
    """
    brcid_mapping = {}
    files = []
    
    if pin_ref is not None:
        brcid_mapping, files = get_brcid_mapping(pin, pin_ref)
    else:
        files = get_corpus_files(pin)
        brcid_mapping = {f.split('\\')[-1]: f.split('\\')[1] for f in files}

    xml = [f for f in files if 'xml' in f]
    
    if df is None:
        df = pd.DataFrame(columns=['filename', 'brcid', key])
        df['filename'] = xml
    
    for i, f in enumerate(xml):
        fname = f.split('\\')[-1]
        brcid = brcid_mapping.get(fname)
        mentions = load_mentions_with_attributes(f)
        mentions = convert_file_annotations(mentions)
        mentions = [m for m in mentions if m.get('status', None) == 'RELEVANT' and \
                    m.get('polarity', None) == 'POSITIVE' and \
                    m.get('temporality', None) == 'CURRENT']
        #m_string = ''
        #for m in mentions:
        #    if m.get(attribute, None) is not None:
        #        m_string += '|' + m[attribute]
        #    else:
        #        print(m)
        m_string = '|'.join([m[attribute] for m in mentions if m[attribute]])
        df.at[i, key] = m_string
        df.at[i, 'brcid'] = brcid
    
    return df, brcid_mapping, files


def count_flagged_patients(df_processed, key, cohort='restricted', attribute='text', split_attribute=False, verbose=True):
    """
    Apply all filtering heuristics to outputs stored in a DataFrame.
    df_processed: the DataFrame containing the data
    cohort: full or restricted
    attribute: text or sh_type
    split_attribute: True if processing directly from a DataFrame, False if 
                     data is loaded from annotated files (e.g. if called 
                     from within evaluate_patient_level_with_heuristics)
    Outputs can be:
        - boolean: indicating if a document is flagged or not
        - integer: indicates number of relevant (e.g. true) mentions
        - string: the text of all mentions separated by a '|'
    """
    
    if cohort not in ['full', 'restricted']:
        raise ValueError('-- Invalid cohort:', cohort, 'choose "full" or "restricted"')
    
    # make sure type for brcid is string
    df_processed['brcid'] = df_processed.brcid.astype(int).astype(str)

    if cohort == 'restricted':
        df = pd.read_excel('T:/Andre Bittar/Projects/KA_Self-harm/Data/SHever_no_temporality_full_restricted.xlsx')
        df = df.loc[df.restricted == 1]
        df['brcid'] = df.brcid.astype(int).astype(str) # type as string
        df_processed = df_processed.loc[df_processed.brcid.isin(df.brcid)]

    n_patients = df_processed.brcid.unique().shape[0]
    results = {}
    data_type = str(df_processed[key].dtype)

    if data_type == 'object':
        key_int = key + '_int'
        counts = [len(y) for y in df_processed[key].apply(lambda x: x.split('|') if x != '' else []).tolist()]
        df_processed[key_int] = counts
        
        # any document with at least one true mention
        flagged = list(set(df_processed.loc[df_processed[key_int] > 0].brcid.tolist()))
        results['1m_doc'] = [str(int(x)) for x in flagged]
        
        # any document with at least two true mentions
        flagged = list(set(df_processed.loc[df_processed[key_int] > 1].brcid.tolist()))
        results['2m_doc'] = [str(int(x)) for x in flagged]
        
        base = []
        tm = []
        tmd = []
        tmd_doc = []
        tmds = []
        tmds_doc = []
        for g in df_processed.groupby('brcid'):
            brcid = g[0]
            for i, row in g[1].iterrows():
                # any patient with any document with at least two mentions with different text/attribute value
                if split_attribute:
                    if attribute == 'text':
                        true_texts = [x.split('#')[0] for x in row[key].split('|') if x != '']
                    else:
                        # use the attribute value - mention text must previously have been stored in the format text:attr_value (e.g. overdose#OVERDOSE)
                        true_texts = [x.split('#')[1] for x in row[key].split('|') if x != '']
                else:
                    true_texts = row[key].split('|')
                if len(set(true_texts)) > 1:
                    tmd_doc.append(brcid)
                if len(true_texts) > 1 and len(set(true_texts)) == len(true_texts):
                    tmds_doc.append(brcid)
            text_list = [x.split('|') for x in g[1][key].tolist() if x != '']
            # flatten the list
            if split_attribute:
                if attribute == 'text':
                    true_texts = [item.split('#')[0] for sublist in text_list for item in sublist]
                else:
                    true_texts = [item.split('#')[1] for sublist in text_list for item in sublist]
            else:
                true_texts = [item for sublist in text_list for item in sublist]
            # any patient with at least one true mention
            if len(true_texts) > 0:
                base.append(brcid)
            # any patient with at least two true mentions
            if len(true_texts) > 1:
                tm.append(brcid)
            # any patient with at least two true mentions with different text
            if len(set(true_texts)) > 1:
                tmd.append(brcid)
            # any patient with at least two true mentions and all mentions with different text
            if len(true_texts) > 1 and len(set(true_texts)) == len(true_texts):
                tmds.append(brcid)
        results['1m_patient'] = list(set(base))
        results['2m_patient'] = list(set(tm))
        results['2m_diff_doc'] = list(set(tmd_doc))
        results['2m_diff_patient'] = list(set(tmd))
        results['2m_diff_strict_doc'] = list(set(tmds_doc))
        results['2m_diff_strict_patient'] = list(set(tmds))
        
    elif 'int' in data_type or 'float' in data_type:
        # any document with at least one true mention
        flagged = list(set(df_processed.loc[df_processed[key] > 0].brcid.tolist()))
        results['1m_doc'] = flagged

        # any document with at least two true mentions
        flagged = list(set(df_processed.loc[df_processed[key] > 1].brcid.tolist()))
        results['2m_doc'] = flagged

    elif data_type == 'bool':
        flagged = list(set(df_processed.loc[df_processed[key] == True].brcid.tolist()))
        results['1m_doc'] = flagged

    n = 1
    df_pat_res = pd.DataFrame(columns=['heur', 'n_flagged', 'n', '%_flagged'])
    for heur in HEURISTICS:
        if heur in results:
            x = len(results[heur]) / n_patients * 100
            df_pat_res.loc[n, ['heur', 'n_flagged', 'n', '%_flagged']] = [heur, len(results[heur]), n_patients, x]
            n += 1
                
    if verbose:
        print(df_pat_res)
    else:
        print('-- Heuristics not in results (skipping):', heur)
    
    return results, df_pat_res


def evaluate_patient_level_with_heuristics(pin_gold, pin_sys, attribute='text', report_dir=None):
    """
    Evaluate patient-level against an annotated gold standard.
    pin_gold = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev'
    pin_sys = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev'
    """
    report_string =  '===============================\n'
    report_string += 'PATIENT-LEVEL EVALUATION REPORT\n'
    report_string += '===============================\n\n'
    
    report_string += 'Gold  : ' + pin_gold + '\n'
    report_string += 'System: ' + pin_sys + '\n\n'
    
    key_gold = 'gold'
    
    # the gold corpus should not have the attribute specified as it does not 
    # have annotated attributes and the heuristics are not applied to it.
    df_gold, _, _ = load_ehost_to_dataframe(pin_gold, key_gold, df=None, pin_ref='T:/Andre Bittar/Projects/KA_Self-harm/Corpus_full')
    df_gold['brcid'] = df_gold.brcid.astype(int).astype(str)
    
    gold_brcids = set(df_gold.loc[df_gold[key_gold] != ''].brcid.unique().tolist())
    
    # build a DataFrame with all BRCIDs and their flags
    all_brcids = sorted(df_gold.brcid.unique().tolist())
    df_gold_brcids = pd.DataFrame()
    df_gold_brcids['brcid'] = all_brcids
    df_gold_brcids['flag'] = False
    df_gold_brcids.loc[df_gold_brcids.brcid.isin(gold_brcids), 'flag'] = True
    
    # percentage prevalence in the gold standard
    n_total = len(all_brcids)
    gold_np = round(len(gold_brcids) / len(all_brcids) * 100, 2)
    
    key_sys = 'system'
    df_sys, _, _ = load_ehost_to_dataframe(pin_sys, key_sys, attribute=attribute, df=None, pin_ref='T:/Andre Bittar/Projects/KA_Self-harm/Corpus_full')
    
    # count patients flagged by the system for each heuristic and output results. Do not use restricited cohort here as
    # not all patients in manually annotated sample are in the restricted cohort
    res_sys, _ = count_flagged_patients(df_sys, key_sys, cohort='full', attribute=attribute, split_attribute=False, verbose=False)
    
    # check the brcids are strings
    assert set([type(item) for sublist in res_sys.values() for item in sublist]) == {str}
    assert df_gold_brcids.brcid.dtype == 'O'
    
    results_dict = {}
    
    for heur in res_sys:
        df_gold[heur] = False
        for brcid in res_sys[heur]:
            # calculate boolean value for each document, store in gold dataframe
            inds = df_gold.loc[df_gold.brcid == brcid].index
            df_gold.loc[inds, heur] = True

        report_string += 'Heuristic: ' + heur + '\n'
        report_string += '----------' + '-' * len(heur) + '\n'
        system_brcids = []
        for row in df_gold.groupby('brcid'):
            if row[1][heur].iloc[0] == True:
                system_brcids.append(row[0])
        
        # make the lists of brcids into sets for following operations
        #gold_brcids = set(gold_brcids)
        system_brcids = set(system_brcids)

        # create DataFrame for system flags
        df_sys_brcids = pd.DataFrame()
        df_sys_brcids['brcid'] = all_brcids
        df_sys_brcids['flag'] = False
        df_sys_brcids.loc[df_sys_brcids.brcid.isin(system_brcids), 'flag'] = True
        
        fn = len(gold_brcids.difference(system_brcids))
        fp = len(system_brcids.difference(gold_brcids))
        tp = len(gold_brcids.intersection(system_brcids))

        sys_n = len(system_brcids)
        sys_np = round(len(res_sys[heur]) / len(all_brcids) * 100, 2)
        report_string += 'Gold prevalence     : ' + str(len(gold_brcids)) + '/' + str(n_total) + ' (' + str(gold_np) + '%)\n'
        report_string += 'System prevalence   : ' + str(sys_n) + '/' + str(n_total) + ' (' + str(sys_np) + '%)\n'
        report_string += 'Gold and System (TP): ' + str(tp) + '\n'
        report_string += 'Gold not System (FN): ' + str(fn) + '\n'
        report_string += 'System not Gold (FP): ' + str(fp) + '\n'
        y_true = df_gold_brcids.flag
        y_pred = df_sys_brcids.flag
        cr = classification_report(y_true, y_pred)
        cr_d = classification_report(y_true, y_pred, output_dict=True)
        p = cr_d['True']['precision']
        r = cr_d['True']['recall']
        f = cr_d['True']['f1-score']
        report_string += cr
        k = round(cohen_kappa_score(y_true, y_pred), 2)
        results_dict[heur] = {'p': p, 'r': r, 'f': f, 'k': k, 'sys_n': sys_n, 'sys_%': sys_np}
        report_string += '       kappa       ' + str(k) + '\n'
        report_string += '====================\n\n'
    
    # select best results
    df_results = pd.DataFrame(results_dict).T.reset_index()
    df_results.rename(columns={'index': 'heuristic'}, inplace=True)   
    df_results = df_results[['heuristic', 'p', 'r', 'f', 'k', 'sys_n', 'sys_%']]
    df_results['sys_n'] = df_results.sys_n.astype(int)
    df_results = df_results.round(2)

    report_string += 'Global Summary\n'
    report_string += '--------------\n\n'

    report_string += 'Total patients                   : ' + str(len(all_brcids)) + '\n'
    report_string += 'Actual prevalence (gold standard): ' + str(len(gold_brcids)) + ' (' + str(gold_np) + '%)\n\n'
    report_string += str(df_results)
    
    print(report_string)    
    
    if report_dir is not None:
        today = str(date.today())
        label = os.path.basename(os.path.normpath(pin_gold))
        pout = os.path.join(report_dir, 'patient-level_evaluation_report_' + label + '_' + attribute + '_' + today + '.txt')
        fout = open(pout, 'w')
        print('-- Printed report to file:', pout, file=sys.stderr)
        fout.write(report_string)
        fout.close()
    
    return df_results


def process(pin, check_counts=True, check_temporality=True, heuristic='base', test_rows=-1):
    """
    Run sh_annotator on a DataFrame that contains the text for each file.
    Outputs True for documents with relevant mention.
    Does not write new XML.
    All saved to the DataFrame.
    """
    
    now = str(date.today()).replace('-', '')

    if check_temporality:
        now += '_tmp'
    else:
        now += '_notmp'
    
    # temporary save file
    tmp_pout = os.path.join(os.path.dirname(pin), 'tmp_' + now + '.pickle')
    
    sha = SHAnnotator(verbose=False)
    #df = pd.read_pickle('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle')
    df = pd.read_pickle(pin)
    if test_rows > 0:
        df = df[0:test_rows]
    #df['sh'] = False
    n = len(df)
    
    t0 = time()
    for i, row in df.iterrows():
        docid = row.cn_doc_id
        text = row.text_content
        mentions = sha.process_text(text, docid, write_output=False)
        if check_counts:
            if heuristic in ['base', '2m']:
                df.at[i, 'sh_' + now] = count_true_SH_mentions(mentions, check_temporality=check_temporality)
            else:
                text = get_true_SH_mentions(mentions, check_temporality=check_temporality)
                #print(i, docid, text)
                df.at[i, 'sh_' + now] = text
        else:
            df.at[i, 'sh_' + now] = has_SH_mention(mentions, check_temporality=check_temporality)
        if i % 1000 == 0:
            print(i, '/', n)
        if i % 10000 == 0 and test_rows == -1:
            print('-- Creating backup:', tmp_pout)
            df.to_pickle(tmp_pout)

    t1 = time()
    
    print(t1 - t0)
    
    if test_rows == -1:
        move(tmp_pout, pin)
        print('-- Wrote file:', pin)
        df.to_pickle(pin)
    
    return df


if __name__ == '__main__':
    print('-- Check has_SH_mention() internal settings...', file=sys.stderr)
    print('-- Check process() internal settings...', file=sys.stderr)
    print('-- Run one of the two functions...', file=sys.stderr)
    #test(check_temporality=True)
    #df_processed = process('Z:/Andre Bittar/Projects/KA_Self-harm/data/all_text_processed.pickle', check_counts=True, check_temporality=True, heuristic='2m_diff')
    #batch_process('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev_patient/files')
