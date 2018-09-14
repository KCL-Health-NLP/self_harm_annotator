from spacy.tokens import Token

#################################
# Custom attribute declarations #
#################################

Token.set_extension('DSH', default=False)
Token.set_extension('TEST1', default=False)
Token.set_extension('TEST2', default=False)
Token.set_extension('TEST3', default=False)
Token.set_extension('TEST4', default=False)

####################
# Rule definitions #
####################

RULES = [
    {
        'name': 'CUT_HER_X_ARM',
        'pattern': [{'LOWER': 'cut'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'TRUE'}, 1: {'DSH': 'TRUE'}, 2: {'DSH': 'TRUE'}}
    },
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
]