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
    # suicidal NON-RELEVANT
    {
        # suicidal ideation
        'name': 'SUICIDAL_IDEATION',
        'pattern': [{'LEMMA': {'REGEX': '^(suicid(e|al))$'}}, {'LEMMA': {'REGEX': '^(idea(tion)?|thought)'}}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # suicidal intention
        'name': 'SUICIDAL_INTENTION',
        'pattern': [{'LEMMA': {'REGEX': '^(suicid(e|al))$'}}, {'_': {'LA': 'INTENT'}}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # plans for suicide
        'name': 'PLAN_FOR_SUICIDE',
        'pattern': [{'LEMMA': 'plan'}, {'LEMMA': {'IN': ['for', 'of']}}, {'LEMMA': 'suicide'}],
        'avm': {2: {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # thought of suicide
        'name': 'THOUGHT_OF_SUICIDE',
        'pattern': [{'LEMMA': {'REGEX': '^(dream|thought)$'}}, {'LEMMA': {'REGEX': '^(about|of)$'}}, {'LEMMA': 'suicide'}],
        'avm': {0: {'DSH': False}, 'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # wanted to die
        'name': 'WANT_TO_DIE',
        'pattern': [{'LEMMA': 'want'}, {'LEMMA': 'to'}, {'LEMMA': 'die'}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # felt suicidal
        'name': 'FEEL_SUICIDAL',
        'pattern': [{'LEMMA': 'feel'}, {'LEMMA': 'suicidal'}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    # suicide pattern rules - add LA=SUICIDE annotation
    {
        # commit suicide
        'name': 'COMMIT_SUICIDE',
        'pattern': [{'LEMMA': 'commit'}, {'LEMMA': 'suicide'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False
    },
    {
        # end her (own) life
        'name': 'END_HER_LIFE',
        'pattern': [{'LEMMA': {'IN': ['end', 'take']}}, {'LEMMA': 'her'}, {'LEMMA': 'own', 'OP': '?'}, {'LEMMA': 'life'}],
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
    {
        # attempt(ed) suicide
        'name': 'ATTEMPT_SUICIDE',
        'pattern': [{'LEMMA': 'attempt'}, {'LEMMA': 'suicide'}],
        'avm': {'ALL': {'LA': 'SUICIDE'}},
        'merge': False
    },
    # DSH pattern rules
    {
        # self harm/ suicide
        'name': 'HARM_LEMMA',
        'pattern': [{'LEMMA': 'self'}, {'LEMMA': { 'REGEX': 'harm\W'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
    },
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
        # pull her hair
        'name': 'PULL_HER_HAIR',
        'pattern': [{'LEMMA': {'REGEX': '^(pull(ing)?|tug(ging)?|yank(ing)?)'}}, {'LEMMA': 'her'}, {'LEMMA': 'hair'}],
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
        # (deliberately) harm herself (deliberately)
        'name': 'HARM_V_HERSELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'harm'}, {'LEMMA': 'herself'}, {'_': {'LA': 'INTENT'}, 'OP': '*'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberately) harm self (deliberately)
        'name': 'HARM_SELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'harm'}, {'LEMMA': 'self'}, {'_': {'LA': 'INTENT'}, 'OP': '*'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberately) harm her self (deliberately)
        'name': 'HARM_V_HER_SELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'harm'}, {'LEMMA': 'her'}, {'LEMMA': 'self'}, {'_': {'LA': 'INTENT'}, 'OP': '*'}],
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
        'name': 'DELIBERATELY_INJURE_HERSELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '+'}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'herself'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # deliberate injuries
        'name': 'DELIBERATE_INJURY',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '+'}, {'LEMMA': {'IN': ['harm', 'injury', 'violence']}, 'POS': 'NOUN'}, {'LEMMA': 'herself', 'OP': '?'}],
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
        # (deliberate) self-injurious (behaviour)
        'name': 'DSH_2',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': {'REGEX': '^(self-.+)$'}, '_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # self- harmer
        'name': 'SELF-HARMER',
        'pattern': [{'LEMMA': {'REGEX': '^(self-)$'}}, {'LEMMA': 'harmer'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) self- harm (behaviour)
        'name': 'DSH_3',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': {'REGEX': '^(self-?)$'}}, {'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # (deliberate) self harm (behaviour)
        'name': 'DSH_4',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'self'}, {'LEMMA': {'REGEX': '^(harm(ing)?)$'}}, {'LEMMA': 'behaviour', 'OP': '?'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
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
        # took 12 paracetamol tablets
        'name': 'TAKE_NUM_MED_TABLETS',
        'pattern': [{'LEMMA': 'take'}, {'LEMMA': {'>=': 10}}, {'_': {'LA': 'MED'}}, {'LEMMA': {'IN': ['pill', 'tablet']}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # took 28x paracetamol tablets
        'name': 'TAKE_NUM_MED_TABLETS',
        'pattern': [{'LEMMA': 'take'}, {'LEMMA': {'REGEX': '(1[0-9]+|[2-9]+)[Xx]'}}, {}, {'LEMMA': {'IN': ['pill', 'tablet']}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # took 12 tablets of paracetamol
        'name': 'TAKE_NUM_MED_TABLETS',
        'pattern': [{'LEMMA': 'take'}, {'LEMMA': {'>=': 10}}, {'LEMMA': {'IN': ['pill', 'tablet']}}, {'LEMMA': 'of'}, {'_': {'LA': 'MED'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # took a pack of paracetamol tablets
        'name': 'TAKE_NUM_PACK_MED_TABLETS',
        'pattern': [{'LEMMA': 'take'}, {'POS': {'IN': ['DET', 'NUM']}}, {'POS': 'ADJ', 'OP': '?'}, {'LEMMA': {'IN': ['box', 'pack', 'packet']}}, {'LEMMA': 'of'}, {'_': {'LA': 'MED'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
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
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'jump'}, {'LEMMA': {'IN': ['from', 'off', 'out']}}],
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
        # (deliberate) throw herself in front of
        'name': 'THROW_HERSELF',
        'pattern': [{'_': {'LA': 'INTENT'}, 'OP': '*'}, {'LEMMA': 'throw'}, {'LEMMA': 'herself'}, {'POS': {'IN': ['ADP', 'PART']}, 'OP': '+'}],
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
    },
    {
        # suicidal behaviour
        'name': 'SUICIDAL_BEHAVIOUR',
        'pattern': [{'LEMMA': {'REGEX': '^(suicid(al|e))$'}}, {'LEMMA': {'REGEX': '^(act|action|attempt|behaviour|gesture)$'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # suicidal thoughts or attempts
        'name': 'SUICIDAL_N_CONJ_N',
        'pattern': [{'LEMMA': {'REGEX': '^(suicid(al|e))$'}}, {'POS': {'REGEX': '^N'}}, {'POS': 'CCONJ'}, {'POS': 'NOUN', 'LEMMA': {'REGEX': '^(act|action|attempt|behaviour|gesture)$'}}],
        'avm': {0: {'DSH': 'DSH'}, 1: {'DSH': 'DSH'}, 'LAST': {'DSH': 'DSH'}},
        'merge': False
    },
    {
        # violence to self
        'name': 'VIOLENCE_TO_SELF',
        'pattern': [{'LEMMA': 'violence'}, {'LEMMA': 'to'}, {'LEMMA': {'REGEX': '^(her)?self$'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': False
    }
]