from spacy.tokens import Token

# TODO add possibility of setting new attributes for merged spans in the rules

#################################
# Token sequence rules, Level 1 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

RULES_TIME = [
    # Temporal pre-tagging
    {
         # 2/7 ago
        'name': 'NUM_AGO',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'year', 'OP': '?'}, {'LEMMA': 'ago'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # 5 years ago
        'name': 'NUM_YEAR_AGO',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': 'year'}, {'LEMMA': {'IN': ['ago', 'before', 'previously', 'prior']}}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # 4-5 days ago (for incorrect tokenisation)
        'name': 'REGEX_NPRESENT_AGO',
        'pattern': [{'LEMMA': {'REGEX': '.*(day|week|month)'}}, {'LEMMA': 'ago'}],
        'avm': {'ALL': {'TIME': 'PRESENTT'}},
        'merge': False
    },
    {
         # 2 months ago
        'name': 'NUM_NPRESENT_AGO',
        'pattern': [{'POS': 'NUM'}, {'LEMMA': {'IN': ['day', 'week', 'month']}}, {'LEMMA': 'ago'}],
        'avm': {'ALL': {'TIME': 'PRESENTT'}},
        'merge': False
    },
    {
         # at (the) (age) (of) 16
        'name': 'AT_AGE_X',
        'pattern': [{'LEMMA': 'at'}, {'LEMMA': 'the', 'OP': '?'}, {'LEMMA': 'age', 'OP': '?'}, {'LEMMA': 'of', 'OP': '?'}, {'POS': 'NUM'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # aged 16
        'name': 'AGED_X',
        'pattern': [{'LOWER': 'aged'}, {'POS': 'NUM'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # when she was 28
        'name': 'WHEN_SHE_WAS_PAST',
        'pattern': [{'LEMMA': 'when'}, {'LEMMA': {'IN': ['she', 'he', 'they']}}, {'LEMMA': 'be'}, {'POS': 'NUM'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # when she was a kid
        'name': 'WHEN_SHE_WAS_LIFE_STAGE',
        'pattern': [{'LEMMA': 'when'}, {'LEMMA': {'IN': ['she', 'he', 'they']}}, {'LEMMA': 'be'}, {'LEMMA': 'a', 'OP': '?'}, {'_': {'TIME': 'LIFE_STAGE'}}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # in her teens
        'name': 'IN_LIFE_STAGE',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': {'IN': ['her', 'his', 'their'], 'OP': '?'}}, {'_': {'TIME': 'LIFE_STAGE'}}, {'LEMMA': 'year', 'OP': '?'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # as a child
        'name': 'AS_A_LIFE_STAGE',
        'pattern': [{'LEMMA': 'as'}, {'LEMMA': 'a'}, {'_': {'TIME': 'LIFE_STAGE'}}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # in 2002
        'name': 'IN_YEAR',
        'pattern': [{'POS': 'ADP'}, {'LEMMA': {'REGEX': '(19[0-9][0-9]|2[01][0-9][0-9])'}}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # for (over) 12 years
        'name': 'FOR_N_YEARS',
        'pattern': [{'LEMMA': 'for'}, {'LEMMA': 'over', 'OP': '?'}, {'LEMMA': 'more', 'OP': '?'}, {'LEMMA': 'than', 'OP': '?'}, {'POS': 'NUM'}, {'LEMMA': 'year'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    {
         # for (over) a year
        'name': 'FOR_A_YEAR',
        'pattern': [{'LEMMA': 'for'}, {'LEMMA': 'over', 'OP': '?'}, {'LEMMA': 'more', 'OP': '?'}, {'LEMMA': 'than', 'OP': '?'}, {'LEMMA': 'a'}, {'LEMMA': 'year'}],
        'avm': {'ALL': {'TIME': 'PAST'}},
        'merge': False
    },
    # Temporal attribute transfer rules
    {
         # history of self-harm
        'name': 'HISTORY_OF_SH',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'LEMMA': 'of'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # history of trying to self-harm
        'name': 'HISTORY_OF_TRY_TO_SH',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'LEMMA': 'of'}, {'POS': 'VERB'}, {'LEMMA': 'to', 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # history of self-harm
        'name': 'HISTORY_SH',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {1: {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # history of taking overdoses
        'name': 'HISTORY_OF_TAKING_OD',
        'pattern': [{'_': {'TIME': 'PAST'}}, {'LEMMA': 'of'}, {'LEMMA': 'take'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # she has self-harmed in the past
        'name': 'SH_IN_THE_PAST',
        'pattern': [{'_': {'SH': 'SH'}}, {'LEMMA': 'in'}, {'_': {'TIME': 'PAST'}, 'OP': '+'}],
        'avm': {0: {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # she self-harm 5 years ago
        'name': 'SH_PAST',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'_': {'TIME': 'PAST'}, 'OP': '+'}],
        'avm': {0: {'TIME': 'HISTORICAL'}},
        'merge': False
    },
    {
         # she self-harmed over a period of several years in the past
        'name': 'SH_NO_V_PAST',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'POS': {'REGEX': '^[^V]'}, 'OP': '+'}, {'_': {'TIME': 'PAST'}, 'OP': '+'}],
        'avm': {0: {'TIME': 'HISTORICAL'}},
        'merge': False
    }
]