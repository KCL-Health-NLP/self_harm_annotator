# -*- coding: utf-8 -*-
"""
    This is a utility script to calculate agreement for Karyn Ayre's project.
"""

from ehost_annotation_reader import convert_file_annotations, get_corpus_files, load_mentions_with_attributes

__author__ = "André Bittar"
__copyright__ = "Copyright 2020, André Bittar"
__credits__ = ["André Bittar"]
__license__ = "GPL"
__email__ = "andre.bittar@kcl.ac.uk"


def has_DSH_mention(mentions):
    """
    Check if a given set of annotated mentions contains a true DSH mention,
    as per the project's definition, namely polarity=POSITIVE, status=RELEVANT,
    temporality=CURRENT
    
    Arguments:
        - mentions: dict; a dictionary containing all annotated mentions for a
                    document

    Return:
        - bool: True if true mention is found, else False
    """
    mentions = convert_file_annotations(mentions)
    for mention in mentions:
        polarity = mention.get('polarity', None)
        status = mention.get('status', None)
        temporality = mention.get('temporality', None)

        if polarity == 'POSITIVE' and \
            status == 'RELEVANT' and \
            temporality == 'CURRENT':
                return True
    return False


def get_brcid_mapping(ctype):
    """
    Determine the BRCIDs for each file in the gold standard corpus. To get 
    results use 'train_dev' as gold and 'system_train_dev' as system.
    
    Arguments:
        - ctype: str; the corpus type ('sys' for the system annotations, 'gold'
                 for the manually annotated corpus)

    Return:
        - brcid_mapping: dict; the mapping of BRCIDs
        - files: list; the list of files in the corpus
    """
    if ctype == 'gold':
        files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/train_dev')
    elif ctype == 'system':
        files = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Adjudication/system_train_dev')
    files_trunc = [f.split('\\')[-1] for f in files if 'xml' in f]
    
    brcid_mapping = {}
    
    ref = get_corpus_files('T:/Andre Bittar/Projects/KA_Self-harm/Corpus_full')
    ref = [k for k in ref if 'xml' in k]
    
    # get the brcids from the original directory structure
    for f in ref:
        s = f.split('\\')
        brcid = s[1]
        fname = s[3]
        if fname in files_trunc:
            brcid_mapping[fname] = brcid
    
    return brcid_mapping, files


def evaluate_patient_level(brcid_mapping, files):
    """
    Determine patient-level performance on the gold standard corpus.
    
    Arguments:
        - brcid_mapping: dict; a dictionary of BRCID mappings
        - files: list; a list of files in a corpus
    
    Return:
        - relevant_brcids: list; the list of BRCIDs for which a true DSH mention was found
    """
    
    # count relevant mentions in each file
    relevant_brcids = []
    for f in [x for x in files if 'xml' in x]:
        mentions = load_mentions_with_attributes(f)
        if has_DSH_mention(mentions):
            brcid = brcid_mapping.get(f.split('\\')[-1])
            relevant_brcids.append(brcid)
            print(f, brcid)

    return relevant_brcids


if __name__ == '__main__':
    gold_brcid_mapping, gold_files = get_brcid_mapping('gold')
    gold_brcids = set(evaluate_patient_level(gold_brcid_mapping, gold_files))
    
    system_brcid_mapping, system_files = get_brcid_mapping('system')
    system_brcids = set(evaluate_patient_level(system_brcid_mapping, system_files))
    
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