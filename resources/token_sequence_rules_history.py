from spacy.tokens import Token

#################################
# Custom attribute declarations #
#################################

Token.set_extension('HISTORY', default=False, force=True)

#################################
# Token sequence rules, History #
#################################

RULES_HISTORY = [
    {
        # history
        'name': 'HISTORY_COORD',
        'pattern': [{'LOWER': {'IN': ['past', 'previous', 'prior']}, 'OP': '?'}, {'_': {'LA': 'HISTORY_TYPE'}}, {'TAG': 'CC', 'OP': '?'}, {'_': {'LA': 'HISTORY_TYPE'}, 'OP': '?'}, {'LOWER': {'IN': ['background', 'history', 'hx', 'h/o']}}],
        'avm': {'ALL': {'LA': 'HISTORY_TYPE'}},
        'merge': False
    },
    {
        # episodes
        'name': 'EPISODE_HEAD',
        'pattern': [{'LOWER': {'IN': ['historical', 'past', 'previous', 'prior']}}, {'LEMMA': 'episode'}, {'LEMMA': 'of'}],
        'avm': {'ALL': {'LA': 'EPISODE'}},
        'merge': False
    },
    {
        # history
        'name': 'HISTORY_1',
        'pattern': [{'_': {'LA': 'HISTORY_TYPE'}, 'OP': '+'}, {'LEMMA': {'IN': [':', '-', ';', '-', '—']}, 'OP': '+'}, {'IS_SPACE': False, 'OP': '+'}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # PERSONAL HISTORY
        'name': 'HISTORY_2',
        'pattern': [{'IS_SPACE': True}, {'_': {'LA': 'HISTORY_TYPE'}, 'OP': '+'}, {'IS_SPACE': True}, {'IS_SPACE': False, 'OP': '+'}, {'IS_SPACE': True}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # ---------- Past psychiatric history ---------- (match at least 5 times - don't think spaCy allows .{5,})
        'name': 'HISTORY_3',
        'pattern': [{'ORTH': {'REGEX': '^[-=\///#:_][-=\///#:_][-=\///#:_][-=\///#:_][-=\///#:_]+$'}}, {'_': {'LA': 'HISTORY_TYPE'}, 'OP': '+'}, {'LEMMA': {'IN': [':', '-', ';', '-', '—']}, 'OP': '?'}, {'IS_SPACE': False, 'OP': '+'}, {'ORTH': {'REGEX': '^[-=\///#:_][-=\///#:_][-=\///#:_][-=\///#:_]+$'}}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # Historical: .. .
        'name': 'HISTORICAL_1',
        'pattern': [{'LOWER': 'historical'}, {'LEMMA': 'risk', 'OP': '?'}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': 'self', 'OP': '?'}, {'LEMMA': {'IN': [':', '-', ';', '-', '—']}, 'OP': '+'}, {'IS_SPACE': True, 'OP': '?'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '-', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'LEMMA': '.'}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # Historical: ... SPACE
        'name': 'HISTORICAL_2',
        'pattern': [{'LOWER': 'historical'}, {'LEMMA': 'risk', 'OP': '?'}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': 'self', 'OP': '?'}, {'LEMMA': {'IN': [':', '-', ';', '-', '—']}, 'OP': '+'}, {'IS_SPACE': True, 'OP': '?'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '-', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'IS_SPACE': True}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # History of ... .
        'name': 'HISTORY_4',
        'pattern': [{'LOWER': 'history'}, {'LEMMA': 'of'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '-', '—', 'present']}, 'IS_SPACE': False, 'OP': '+'}, {'LEMMA': {'IN': ['.', '?', '!', '*', '#']}}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # History of ... SPACE
        'name': 'HISTORY_5',
        'pattern': [{'LOWER': 'history'}, {'LEMMA': 'of'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '-', '—', 'present']}, 'IS_SPACE': False, 'OP': '+'}, {'IS_SPACE': True}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # past episodes of ... .
        'name': 'EPISODE_SENT_1',
        'pattern': [{'_': {'LA': 'EPISODE'}, 'OP': '+'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'LEMMA': {'IN': ['.', '?', '!', '*', '#']}}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # past episodes of ... SPACE
        'name': 'EPISODE_SENT_2',
        'pattern': [{'_': {'LA': 'EPISODE'}}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'IS_SPACE': True}, {'IS_SPACE': True}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # historical ... .
        'name': 'HISTORICAL_SENT_1',
        'pattern': [{'LOWER': 'historical'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'LEMMA': {'IN': ['.', '?', '!', '*', '#']}}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     },
     {
        # historical ... SPACE
        'name': 'HISTORICAL_SENT_2',
        'pattern': [{'LOWER': 'historical'}, {'LEMMA': {'NOT_IN': ['.', '?', '!', '*', '#', '—']}, 'IS_SPACE': False, 'OP': '+'}, {'IS_SPACE': True}],
        'avm': {'ALL': {'HISTORY': 'HISTORY'}},
        'merge': False
     }
]