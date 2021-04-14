#################################
# Token sequence rules, Level 2 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

RULES_NEGATION = [
    {
        # no SH
        'name': 'NO_SH',
        'pattern': [{'LEMMA': 'no'}, {'_': {'SH': 'SH'}}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # no discernible evidence/mention/risk/sign/suggestion of SH
        'name': 'NO_X_OF_SH',
        'pattern': [{'LEMMA': 'no'}, {'POS': {'REGEX': '^V'}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'LEMMA': 'of'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # never SH
        'name': 'NEVER_SH',
        'pattern': [{'LEMMA': 'never'}, {'POS': {'REGEX': '^V'}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # denies SH
        'name': 'NEVER_SH',
        'pattern': [{'LEMMA': {'IN': ['deny', 'denie']}}, {'POS': 'ADV', 'OP': '*'}, {'LEMMA': {'IN': ['have', 'having']}, 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # not SH
        'name': 'NEVER_SH',
        'pattern': [{'LEMMA': {'IN': ['never', 'not']}}, {'POS': 'ADV', 'OP': '*'}, {'LEMMA': {'IN': ['have', 'having']}, 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # unable to ... SH
        'name': 'UNABLE_X_SH',
        'pattern': [{'LEMMA': 'unable'}, {'LEMMA': 'to'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    }
]
