#################################
# Token sequence rules, Level 3 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

SAVED_RULES = [
    {
         # if she...SH
        'name': 'IF_SHE_SH',
        'pattern': [{'LEMMA': 'if'}, {'LEMMA': 'she'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': False
    }
]

RULES_STATUS = [
    {
         # history of self-harm?
        'name': 'SH_QUESTION',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'LEMMA': '?'}],
        'avm': {'ALL': {'SH': False}},
        'merge': False
    },
    {
         # he...made suicide attempts
        'name': 'HE_SH',
        'pattern': [{'LOWER': 'he'}, {'LEMMA': {'NOT_IN': ['she', 'her', 'herself', 'zzzzz', '.', '?', '!', ':', ';']}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': False
    },
    {
         # plan to...hang herself
        'name': 'PLAN_TO_SH',
        'pattern': [{'LEMMA': {'IN': ['intend', 'plan']}}, {'LEMMA': 'to'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'SH': {'NOT_IN': ['SH']}}, 'OP': '+'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': False
    }
]