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

""" NOT WORKING IN THIS VERSION OF SPACY
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
        'avm': {0: {'TIME': 'TRUE'}, 1: {'TIME': 'TRUE'}}
    }
]