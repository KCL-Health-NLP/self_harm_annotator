#################################
# Token sequence rules, Level 3 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

SAVED_RULES = [
    {
         # if she...DSH
        'name': 'IF_SHE_DSH',
        'pattern': [{'LEMMA': 'if'}, {'LEMMA': 'she'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': False
    }
]

RULES_STATUS = [
    {
         # history of self-harm?
        'name': 'DSH_QUESTION',
        'pattern': [{'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': '?'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': False
    },
    {
         # he...made suicide attempts
        'name': 'HE_DSH',
        'pattern': [{'LOWER': 'he'}, {'LEMMA': {'NOT_IN': ['she', 'her', 'herself', 'zzzzz', '.', '?', '!', ':', ';']}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': False
    },
    {
         # plan to...hang herself
        'name': 'PLAN_TO_DSH',
        'pattern': [{'LEMMA': {'IN': ['intend', 'plan']}}, {'LEMMA': 'to'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', ':', ';']}, '_': {'DSH': {'NOT_IN': ['DSH']}}, 'OP': '+'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': False
    }
]