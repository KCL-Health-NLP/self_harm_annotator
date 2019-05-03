from spacy.tokens import Token

# TODO add possibility of setting new attributes for merged spans in the rules

#################################
# Token sequence rules, Level 1 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

RULES_TIME = [
    # Temporal pre-tagging
    {
         # when she was a kid
        'name': 'WHEN_SHE_WAS_PAST',
        'pattern': [{'LEMMA': 'when'}, {'LEMMA': 'she'}, {'LEMMA': 'be'}, {'LEMMA': 'a', 'OP': '?'}, {'_': {'TIME': 'LIFE_STAGE'}}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    # Temporal attribute transfer rules
    {
         # history of self-harm
        'name': 'HISTORY_OF_DSH',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'LEMMA': 'of'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # history of taking overdoses
        'name': 'HISTORY_OF_TAKING_OD',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'LEMMA': 'of'}, {'LEMMA': 'take'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         
        'name': 'DSH_IN_THE_PAST',
        'pattern': [{'_': {'DSH': 'DSH'}}, {'LEMMA': 'in'}, {'_': {'TIME': 'PAST'}, 'OP': '+'}],
        'avm': {0: {'TIME': 'HISTORICAL'}},
        'merge': False
    }
]