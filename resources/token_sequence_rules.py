from spacy.tokens import Token

#################################
# Custom attribute declarations #
#################################

Token.set_extension('DSH', default=False, force=True)
Token.set_extension('TIME', default=False, force=True)

""" TESTS
Token.set_extension('TEST1', default=False)
Token.set_extension('TEST2', default=False)
Token.set_extension('TEST3', default=False)
Token.set_extension('TEST4', default=False)

    {
        'name': 'TEST_1',
        'pattern': [{'LEMMA': 'be'}, {'POS': 'ADV', 'OP': '*'}, {'POS': 'ADJ'}],
        'avm': {0: {'TEST1': 'TRUE'}, 1: {'TEST2': 'TRUE'}, 2: {'TEST3': 'TRUE'}}
    },
    {
        'name': 'TEST_2',
        'pattern': [{'_': {'DSH': 'TRUE'}}],
        'avm': {0: {'TEST4': 'TRUE'}}
    }
"""

""" NOT WORKING IN THIS VERSION OF SPACY, REGEX not yet implemeneted
    {
        'name': 'CUT_HER_X_ARM',
        'pattern': [{'LEMMA': 'cut'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'BURN_HER_X_ARM',
        'pattern': [{'LEMMA': 'burn'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'SLASH_HER_X_ARM',
        'pattern': [{'LEMMA': 'slash'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'LACERATE_HER_X_ARM',
        'pattern': [{'LEMMA': 'lacerate'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'HIT_HER_X_ARM',
        'pattern': [{'LEMMA': 'hit'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'PUNCH_HER_X_ARM',
        'pattern': [{'LEMMA': 'punch'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'HIT_HERSELF_IN_X_ARM',
        'pattern': [{'LEMMA': 'hit'}, {'LOWER': 'herself'}, {'POS': 'ADP'}, {'POS': 'DET'},
                    {'REGEX': '^(arms?|hands?|legs?|chest|breasts|stomach|face)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
    {
        'name': 'PUNCH_HERSELF_IN_X_ARM',
        'pattern': [{'LEMMA': 'punch'}, {'LOWER': 'herself'}, {'POS': 'ADP'}, {'POS': 'DET'},
                    {'REGEX': '^(arms?|hands?|legs?|chest|breasts|stomach|face)'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}}
    },
"""


####################
# Rule definitions #
####################

RULES = [
    {
        'name': 'IN_YEAR',
        'pattern': [{'POS': 'ADP'}, {'SHAPE': 'dddd'}],
        'avm': {0: {'TIME': 'TIME'}, 1: {'TIME': 'TIME'}}
    },
    {
        'name': 'SINCE_MON',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'monday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_TUE',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'tuesday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_WED',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'wednesday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_THU',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'thursday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_FRI',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'friday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_SAT',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'saturday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'SINCE_SUN',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': 'sunday'}],
        'avm': {0: {'TIME': False}, 1: {'TIME': False}}
    },
    {
        'name': 'IN_MONTH_YEAR',
        'pattern': [{'POS': 'ADP'}, {'POS': 'PROPN'}, {'SHAPE': 'dddd'}],
        'avm': {0: {'TIME': 'TIME'}, 1: {'TIME': 'TIME'}, 2: {'TIME': 'TIME'}}
    },
    # for some reason 'od' was causing bizarre matching in the dsh_sequence_lex, so moved it to here
    {
        'name': 'OD',
        'pattern': [{'ORTH': 'OD'}],
        'avm': {0: {'DSH': 'DSH'}}
    },
    {
        'name': 'MED_DOSAGE_1',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'mg'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'MED_DOSAGE_2',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'mgrs'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'MED_DOSAGE_3',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'milligrams'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'MED_DOSAGE_4',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'milligrammes'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'MED_DOSAGE_5',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'mcg'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'MED_DOSAGE_6',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'gram'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': False}}
    },
    {
        'name': 'DSH',
        'pattern': [{'LEMMA': 'deliberate'}, {'LEMMA': 'self-harm'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'SCRATCH_ON_HER_NN',
        'pattern': [{'LEMMA': 'scratch'}, {'POS': 'ADP'}, {'LEMMA': 'her'}, {'POS': 'NOUN'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'THROW_HERSELF_IN_DET_NOUN',
        'pattern': [{'LEMMA': 'throw'}, {'LEMMA': 'herself'}, {'POS': 'ADP'}, {'POS': 'DET'}, {'POS': 'NOUN'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}, 4: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'THROW_HERSELF_IN_FRONT_OF_DET_NOUN',
        'pattern': [{'LEMMA': 'throw'}, {'LEMMA': 'herself'}, {'POS': 'ADP'}, {'LEMMA': 'front'}, {'LEMMA': 'of'}, {'POS': 'DET'}, {'POS': 'NOUN'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}, 4: {'DSH': 'DSH'}, 5: {'DSH': 'DSH'}, 6: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'JUMP_IN_DET_NOUN',
        'pattern': [{'LEMMA': 'jump'}, {'POS': 'ADP'}, {'POS': 'DET'}, {'POS': 'NOUN'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'KILL_HERSELF',
        'pattern': [{'LEMMA': 'kill'}, {'LEMMA': 'herself'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'HARM_HERSELF',
        'pattern': [{'LEMMA': 'harm'}, {'LEMMA': 'herself'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}},
        'merge': True
    },
    # sometimes this doesn't match from the lexicon
    {
        'name': 'SELF_HARM',
        'pattern': [{'LEMMA': 'self'}, {'LEMMA': 'harm'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'TAKE_HER_OWN_LIFE',
        'pattern': [{'LEMMA': 'take'}, {'LEMMA': 'her'}, {'LEMMA': 'own'}, {'LEMMA': 'life'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'END_HER_LIFE',
        'pattern': [{'LEMMA': 'end'}, {'LEMMA': 'her'}, {'LEMMA': 'life'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'END_HER_OWN_LIFE',
        'pattern': [{'LEMMA': 'end'}, {'LEMMA': 'her'}, {'LEMMA': 'own'}, {'LEMMA': 'life'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}},
        'merge': True
    },
    # suicidal thoughts is merged on lexicon matching
    {
        'name': 'SUICIDAL_THOUGHTS_AND_ACT',
        'pattern': [{'LEMMA': 'suicidal thought'}, {'LEMMA': 'and'}, {'LEMMA': 'act'}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 2: {'DSH': 'DSH'}},
        'merge': True
    },
    {
        'name': 'PLANNED_OD',
        'pattern': [{'ORTH': 'planned'}, {'LEMMA': 'overdose'}],
        'avm': {0: {'HEDGING': False}, 1: {'DSH': 'DSH'}},
        'merge': False
    },
    # This next rule is ad hoc to deal with headings, needs to be generalised
    {
        'name': 'SPACE_DSH_SPACE',
        'pattern': [{'POS': 'SPACE'}, {'LEMMA': 'self harm'}, {'POS': 'SPACE'}],
        'avm': {1: {'DSH': 'NON_DSH'}},
        'merge': False
    },
    {
        'name': 'RISK_ASSESSMENT',
        'pattern': [{'LEMMA': 'risk'}, {'LEMMA': 'assessment'}],
        'avm': {0: {'HEDGING': False}},
        'merge': False
    },
    {
        'name': 'MG_OD',
        'pattern': [{'ORTH': 'mg'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'MGS_OD',
        'pattern': [{'ORTH': 'mgs'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'MILLIGRAM_OD',
        'pattern': [{'LEMMA': 'milligram'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'MICROGRAM_OD',
        'pattern': [{'LEMMA': 'microgram'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'MICROGRAMME_OD',
        'pattern': [{'LEMMA': 'microgramme'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'G_OD',
        'pattern': [{'LEMMA': 'g'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'GRAMME_OD',
        'pattern': [{'LEMMA': 'gramme'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'GRAM_OD',
        'pattern': [{'LEMMA': 'gram'}, {'LEMMA': 'od'}],
        'avm': {1: {'DSH': 'NO_DSH'}},
        'merge': False
    },
    {
        'name': 'TABLET_OD',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'tablet'}, {'LEMMA': 'od'}],
        'avm': {2: {'DSH': 'NO_DSH'}},
        'merge': False
    }
]