#################################
# Token sequence rules, Level 2 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

RULES_NEGATION = [
    {
        # no DSH
        'name': 'NO_DSH',
        'pattern': [{'LEMMA': 'no'}, {'_': {'DSH': 'DSH'}}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # no discernible evidence/mention/risk/sign/suggestion of DSH
        'name': 'NO_X_OF_DSH',
        'pattern': [{'LEMMA': 'no'}, {'POS': {'REGEX': '^V'}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'LEMMA': 'of'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # never DSH
        'name': 'NEVER_DSH',
        'pattern': [{'LEMMA': 'never'}, {'POS': {'REGEX': '^V'}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # denies DSH
        'name': 'NEVER_DSH',
        'pattern': [{'LEMMA': {'IN': ['deny', 'denie']}}, {'POS': 'ADV', 'OP': '*'}, {'LEMMA': {'IN': ['have', 'having']}, 'OP': '?'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # not DSH
        'name': 'NEVER_DSH',
        'pattern': [{'LEMMA': {'IN': ['never', 'not']}}, {'POS': 'ADV', 'OP': '*'}, {'LEMMA': {'IN': ['have', 'having']}, 'OP': '?'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    },
    {
        # unable to ... DSH
        'name': 'UNABLE_X_DSH',
        'pattern': [{'LEMMA': 'unable'}, {'LEMMA': 'to'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'NEG': 'NEG'}},
        'merge': True
    }
]
