# -*- coding: utf-8 -*-
"""
    This is a utility script to calculate agreement for Karyn Ayre's project.
"""
import pandas as pd

from ehost_annotation_reader import convert_file_annotations, get_corpus_files, load_mentions_with_attributes

#HEURISTICS = ['base', '2m', '2m_diff', '2m_diff_strict']
HEURISTICS = ['1m_doc', '2m_doc', '1m_patient', '2m_patient', '2m_diff_doc', '2m_diff_patient', '2m_diff_strict_doc', '2m_diff_strict_patient']



def has_SH_mention(mentions):
    """
    Check if a given set of annotated mentions contains a true SH mention,
    as per the project's definition, namely polarity=POSITIVE, status=RELEVANT,
    temporality=CURRENT
    
    Arguments:
        - mentions: dict; a dictionary containing all annotated mentions for a
                    document

    Return:
        - bool: True if true mention is found, else False
    """
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        temporality = mention.get('temporality', None)

        if polarity == 'POSITIVE' and \
            status == 'RELEVANT' and \
            temporality == 'CURRENT':
                return True
    return False


def get_brcid_mapping(pin, pin_ref):
    """
    Determine the BRCIDs for each file in the gold standard corpus. To get 
    results use 'train_dev' as gold and 'system_train_dev' as system.
    
    Arguments:
        - pin: str; the path to the corpus directory containing annotations
          i.e. system annotations or gold annotations

    Return:
        - brcid_mapping: dict; the mapping of BRCIDs
        - files: list; the list of files in the corpus
    """
    files = get_corpus_files(pin)
    files_trunc = [f.split('\\')[-1] for f in files if 'xml' in f]
    
    brcid_mapping = {}
    
    #ref = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Corpus_full')
    #ref = get_corpus_files('T:/Andre Bittar/Projects/ASD_TS/ASD_ALL_SUI_POS_AND_FHx')
    ref = get_corpus_files(pin_ref)
    ref = [k for k in ref if 'xml' in k]
    
    # get the brcids from the original directory structure
    for f in ref:
        s = f.split('\\')
        if isinstance(s[1], float):
            brcid = str(int(s[1]))
        else:
            brcid = str(s[1])
        fname = s[3]
        if fname in files_trunc:
            brcid_mapping[fname] = brcid
    
    return brcid_mapping, files


def check_prevalence(files, heuristic, cohort='full'):
    """
    Determine SH prevalence by applying the heuristics to a list of annotated 
    files.
    """

    if cohort not in ['full', 'restricted']:
        raise ValueError('-- Invalid cohort:', cohort, 'choose "full" or "restricted"')

    global_mentions = {}
    xml = [x for x in files if 'xml' in x]
    n = len(xml)

    for i, f in enumerate(xml):
        mentions = load_mentions_with_attributes(f)
        mentions = convert_file_annotations(mentions)
        brcid = f.split('\\')[1]
        tmp = global_mentions.get(brcid, [])
        tmp += mentions
        global_mentions[brcid] = tmp

        if i % 1000 == 0:
            print(i, '/', n)

    if cohort == 'restricted':
        df = pd.read_excel('Z:/Karyn Ayre/Analysis/Restricted cohort/List_of_IDs_restricted_cohort.xlsx')
        restr_brcids = df['brcid'].astype(str).tolist()
        global_mentions = {brcid: global_mentions[brcid] for brcid in restr_brcids if brcid in global_mentions.keys()}

    """Collect true mentions"""
    global_true_mentions = {}
    for brcid in global_mentions:
        anns = global_mentions[brcid]
        for ann in anns:
            polarity = ann['polarity']
            status = ann['status']
            temporality = ann['temporality']
            if polarity == 'POSITIVE' and status == 'RELEVANT' and temporality == 'CURRENT':
                tmp = global_true_mentions.get(brcid, [])
                tmp.append(ann['text'])
                global_true_mentions[brcid] = tmp

    """Apply heuristics"""
    flagged = []
    for brcid in global_true_mentions:
        anns = global_true_mentions[brcid]
        if heuristic == 'base':
            if len(anns) > 0:
                flagged.append(brcid)
        elif heuristic == '2m':
            if len(anns) > 1:
                flagged.append(brcid)
        elif heuristic == '2m_diff':
            if len(anns) > 1 and len(set(anns)) > 1:
                    flagged.append(brcid)
        elif heuristic == '2m_diff_strict':
            if len(anns) > 1 and len(anns) == len(set(anns)):
                    flagged.append(brcid)
    
    print('Flagged patients:', len(flagged), '/', len(global_mentions), len(flagged) / len(global_mentions) * 100)
    
    return global_mentions


def evaluate_patient_level(brcid_mapping, files, heuristic='2m', verbose=False):
    """
    DEPRECATED - use evaluate_patient_level_with_heuristic in self_harm_cohort_annotator.py
    
    Determine patient-level performance on the gold standard corpus.
    
    Arguments:
        - brcid_mapping: dict; a dictionary of BRCID mappings
        - files: list; a list of files in a corpus
        - heuristic: str; the heuristic to apply
              base: at least 1 true mention of SH
              2m_diff: at least 2 true mentions with different text
              2m_diff_strict: at least 2 true mentions all with different text
    
    Return:
        - relevant_brcids: list; the list of BRCIDs for which a true SH mention was found
    """

    if heuristic not in HEURISTICS:
        raise ValueError('-- incorrect heuristic', heuristic)

    print('-- Using heuristic:', heuristic)
    
    # count relevant mentions in each file
    relevant_brcids = []
    for f in [x for x in files if 'xml' in x]:
        mentions = load_mentions_with_attributes(f)
        mentions = convert_file_annotations(mentions)
        if heuristic == 'base':
            if has_SH_mention(mentions):
                brcid = brcid_mapping.get(f.split('\\')[-1])
                relevant_brcids.append(brcid)
                if verbose:
                    print(heuristic, f, brcid)
        else:
            true_text  = []
            for mention in mentions:
                polarity = mention.get('polarity', None)
                status = mention.get('status', None)
                temporality = mention.get('temporality', None)
                if polarity == 'POSITIVE' and \
                    status == 'RELEVANT' and \
                    temporality == 'CURRENT':
                        text = mention['text'] or ''
                        text = text.strip()
                        true_text.append(text)
            text_unique = set(true_text)
            if heuristic == '2m':
                if len(true_text) > 1:
                    brcid = brcid_mapping.get(f.split('\\')[-1])
                    relevant_brcids.append(brcid)
                    if verbose:
                        print(heuristic, f, brcid)
            if heuristic == '2m_diff':
                if len(text_unique) > 1:
                    brcid = brcid_mapping.get(f.split('\\')[-1])
                    relevant_brcids.append(brcid)
                    if verbose:
                        print(heuristic, f, brcid)
            elif heuristic == '2m_diff_strict':
                if len(text_unique) > 1 and len(text_unique) == len(mentions):
                    brcid = brcid_mapping.get(f.split('\\')[-1])
                    relevant_brcids.append(brcid)
                    if verbose:
                        print(heuristic, f, brcid)

    return relevant_brcids

def process(heuristic='base'):
    """
    DEPRECATED - use evaluate_patient_level_with_heuristic in self_harm_cohort_annotator.py

    Run the whole evaluation process with a specific heuristic on the whole cohort.
    NB: gold must use the 'base' heuristic which is 1 true mention to flag a patient
    """
    gold_pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev'
    #gold_pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Restricted_Cohort_100_patients'
    gold_brcid_mapping, gold_files = get_brcid_mapping(gold_pin)
    gold_brcids = set(evaluate_patient_level(gold_brcid_mapping, gold_files, heuristic='base', verbose=False))
    
    system_pin = 'T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev'
    system_brcid_mapping, system_files = get_brcid_mapping(system_pin)
    system_brcids = set(evaluate_patient_level(system_brcid_mapping, system_files, heuristic=heuristic, verbose=False))
    
    fn = len(gold_brcids.difference(system_brcids))
    fp = len(system_brcids.difference(gold_brcids))
    tp = len(gold_brcids.intersection(system_brcids))

    print('Gold           :', len(gold_brcids))
    print('System         :', len(system_brcids))
    print('Gold and System:', tp)
    print('Gold not System:', fn)
    print('System not Gold:', fp)
    
    p = tp / (tp + fp)
    r = tp / (tp + fn)
    f = 2 * p * r / (p + r)
    
    print('Precision     :', p)
    print('Recall        :', r)
    print('F-score       :', f)