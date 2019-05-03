from spacy.tokens import Token

#################################
# Custom attribute declarations #
#################################

Token.set_extension('DSH', default=False, force=True)
Token.set_extension('BODY_PART', default=False, force=True)
Token.set_extension('TIME', default=False, force=True)

# TODO add possibility of setting new attributes for merged spans in the rules

#################################
# Token sequence rules, Level 0 #
#################################

RULES = [
    # suicide pattern rules - add LA=SUICIDE annotation
    {
        # commit suicide
        'name': 'COMMIT_SUICIDE',
        'pattern': [{'LEMMA': 'commit'}, {'LEMMA': 'suicide'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False  # merge here for now, rather than in next level rules (requires longest match selection for OP=+)
    },
    {
        # end her (own) life
        'name': 'END_HER_LIFE',
        'pattern': [{'LEMMA': 'end'}, {'LEMMA': 'her'}, {'LEMMA': 'own', 'OP': '?'}, {'LEMMA': 'life'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False
    },
    {
        # kill herself
        'name': 'KILL_HERSELF',
        'pattern': [{'LEMMA': 'kill'}, {'LEMMA': 'herself'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False
    },
    {
        # suicide attempt
        'name': 'SUICIDE_ATTEMPT',
        'pattern': [{'LEMMA': 'suicide'}, {'LEMMA': 'attempt'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False
    },
    # DSH pattern rules
    {
        # burnt (both) her (upper (left)) arms
        # TODO avoid matching with He punched her back etc.
        'name': 'HARM_ACTION_POSITION_BODY_PART',
        'pattern': [{'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': {'REGEX': '^(all|both)$'}, 'OP': '?'}, {'LEMMA': 'her'}, {'LEMMA': {'REGEX': '^(left|right|lower|upper)$'}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}, 'POS': 'NOUN'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # burnt herself on the (upper (left)) arm
        'name': 'HARM_ACTION_PP_POSITION_BODY_PART',
        'pattern': [{'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'herself'}, {'POS': 'ADP'}, {'POS': 'DET'}, {'LEMMA': {'REGEX': '^(left|right|lower|upper)$'}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # burns on (both) her (upper (left)) arm
        'name': 'HARM_ACTION_PP_HER_POSITION_BODY_PART',
        'pattern': [{'_': {'LA': 'HARM_ACTION'}}, {'POS': 'ADP'}, {'LEMMA': 'both', 'OP': '?'}, {'LEMMA': 'her'}, {'LEMMA': {'REGEX': '^(left|right|lower|upper)$'}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberately) cut herself (deliberately)
        'name': 'HARM_ACTION_V_HERSELF_1',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'herself'}, {'_': {'LA': 'INTENT'}, 'OP': '*'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) cutting of herself
        'name': 'HARM_ACTION_N_HERSELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'of'}, {'LEMMA': 'herself'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) harm to herself
        'name': 'DELIBERATE_HARM_TO_HERSELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': {'REGEX': '^(to(wards?)?)$'}}, {'LEMMA': {'REGEX': '(her)?self'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # deliberate injuries
        'name': 'DELIBERATE_INJURY',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '+'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'herself', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) self-harm (behaviour)
        'name': 'DSH_1',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': {'REGEX': '^(self-.+)$'}, '_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) self harm (behaviour)
        'name': 'DSH_2',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'self'}, {'LEMMA': {'REGEX': '^(self-.+)$'}, '_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) self- harm (behaviour)
        'name': 'DSH_3',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': {'REGEX': '^(self-)$'}}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberately) engage in cutting (behaviour)
        'name': 'ENGAGE_IN_HARM',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': {'REGEX': '^(carry|do|engage|perform)$'}}, {'POS': {'REGEX': '(ADP|PART)'}, 'OP': '?'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}, 4: {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # evidence of cutting (behaviour)
        'name': 'EVIDENCE_OF_HARM',
        'pattern': [{'LEMMA': {'REGEX': '^(evidence|sign)$'}}, {'LEMMA': 'of'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {2: {'DSH': 'DSH'}, 3: {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # she has (deep) (self-) lacerations
        'name': 'SHE_HAS_HARM',
        'pattern': [{'LEMMA': 'she'}, {'LEMMA': {'REGEX': '^(be|display|evidence|have|present|show)$'}, 'OP': '+'}, {'POS': 'ADP', 'OP': '?'}, {'POS': 'ADJ', 'OP': '?'}, {'LEMMA': {'REGEX': '^(self-)$'}, 'OP': '?'}, {'_': {'LA': 'HARM_ACTION'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # (deliberate) jump off
        'name': 'JUMP_OFF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'jump'}, {'POS': {'REGEX': '^(ADP|PART)$'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) jump in front of
        'name': 'JUMP_IN_FRONT',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'jump'}, {'LEMMA': 'in'}, {'LEMMA': 'front'}, {'LEMMA': 'of'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # great risk to herself
        'name': 'RISK_TO_HERSELF',
        'pattern': [{'LEMMA': {'REGEX': '^(elevated?|extreme|great|high|intense|much|serious|worry|worrying)$'}}, {'LEMMA': 'risk'}, {'LEMMA': 'to'}, {'LEMMA': 'herself'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # self-inflicted injuries
        'name': 'SELF-INFLICTED_INJURIES',
        'pattern': [{'LEMMA': {'REGEX': '^(self\-inflict(ing)?)$'}}, {'_': {'LA': 'HARM_ACTION'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    }
]