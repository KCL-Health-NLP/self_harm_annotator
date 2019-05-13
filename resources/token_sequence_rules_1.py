from spacy.tokens import Token

# TODO add possibility of setting new attributes for merged spans in the rules

#################################
# Token sequence rules, Level 1 #
#################################

# NB rules that use custom attributes added in previous rules go here and be applied in a second application

RULES_1 = [
    {
        # DSH and BODY_PART (for coordinated body parts)
        'name': 'DSH_AND_BODY_PART',
        'pattern': [{'_': {'DSH': 'DSH'}}, {'LEMMA': 'and'}, {'LEMMA': {'REGEX': '^(all|both)$'}, 'OP': '?'}, {'LEMMA': 'her', 'OP': '?'}, {'LEMMA': {'REGEX': '^(left|right|lower|upper)$'}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # attempt to DSH
        'name': 'ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'REGEX': '^(attempt|try)$'}}, {'LEMMA': {'REGEX': '^(at|to)$'}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # attempt (at) suicide
        'name': 'ATTEMPT_AT_SUICIDE',
        'pattern': [{'LEMMA': {'REGEX': '^(attempt|try)$'}}, {'LEMMA': 'at', 'OP': '?'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # attempt to commit suicide
        'name': 'ATTEMPT_TO_COMMIT_SUICIDE',
        'pattern': [{'LEMMA': {'REGEX': '^(attempt|try)(ing)?$'}}, {'LEMMA': {'REGEX': '^(at|to)$'}}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # attempt to electrocute herself
        'name': 'ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'REGEX': '^(attempt|try)(ing)?$'}}, {'LEMMA': {'REGEX': '^(at|to)$'}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # voices telling her to kill herself
        'name': 'TELL_TO_ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'REGEX': '^(command|compell|incite|say|tell|urge)$'}}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': 'her'}, {'LEMMA': 'to'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # cuts from self-harm
        'name': 'HARM_ACTION_N_FROM_DSH',
        'pattern': [{'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'from'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # made a suicide attempt
        'name': 'MAKE_SUICIDE_ATTEMPT',
        'pattern': [{'LEMMA': 'make'}, {'POS': {'REGEX': '^(ADJ|DET|NUM)$'}}, {'POS': {'REGEX': '^(ADJ|ADV)$'}, 'OP': '*'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # DSH behaviour
        'name': 'DSH_BEHAVIOUR',
        'pattern': [{'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': {'REGEX': '^(act|action|attempt|behaviour|gesture)$'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
     # DSH NON-RELEVANT
    {
        # thought of self-harm
        'name': 'THOUGHT_OF_DSH',
        'pattern': [{'LEMMA': {'REGEX': '^(dream|thought)$'}}, {'LEMMA': {'REGEX': '^(about|of)$'}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # plan to end her life
        'name': 'PLAN_TO_SUICIDE',
        'pattern': [{'LEMMA': {'REGEX': '^(inten(d|t)|plan)$'}}, {'LEMMA': 'to'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}, 'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # thought of self-harm or suicide
        'name': 'THOUGHT_OF_DSH_OR_SUICIDE',
        'pattern': [{'LEMMA': {'REGEX': '^(dream|thought)$'}}, {'LEMMA': {'REGEX': '^(about|of)$'}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}, {'POS': 'CCONJ'}, {'LEMMA': 'suicide'}],
        'avm': {0: {'DSH': False}, 'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # harmful thoughts
        'name': 'HARMFUL_THOUGHT',
        'pattern': [{'LEMMA': 'harmful'}, {'LEMMA': {'REGEX': '^(thought)$'}}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
     # DSH NON-RELEVANT
    {
        # suicidal or self-harm ideation
        'name': 'SUICIDAL_CCONJ_DSH_IDEATION',
        'pattern': [{'LEMMA': {'REGEX': '^(suicid(al|e))$'}}, {'POS': 'CCONJ'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': 'ideation'}],
        'avm': {0: {'DSH': 'DSH', 'HEDGING': 'HEDGING'}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    # NON-DSH
    {
        # mg OD
        'name': 'OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^(mc?gs?|(micro|mill?i)?gram(me)?|tablet|tabs?)$'}}, {'LEMMA': {'REGEX' : '^(od|OD)'}}],
        'avm': {1: {'DSH': False}},
        'merge': True
     },
     {
        # mg OD
        'name': 'NUMUNIT_OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^[0-9\.,]+(mc?gs?|(micro|mill?i)?gram(me)?)$'}}, {'LEMMA': {'REGEX' : '^(od|OD)'}}],
        'avm': {1: {'DSH': False}},
        'merge': True
     }
]