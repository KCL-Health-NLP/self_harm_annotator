#################################
# Token sequence rules, Level 1 #
#################################

# NB rules that use custom attributes added in previous rules go here and are applied in a second application


RULES_1 = [
    {
        # DSH and BODY_PART (for coordinated body parts)
        'name': 'DSH_AND_BODY_PART',
        'pattern': [{'_': {'DSH': 'DSH'}}, {'LEMMA': 'and'}, {'LEMMA': {'IN': ['all', 'both']}, 'OP': '?'}, {'LEMMA': 'her', 'OP': '?'}, {'LEMMA': {'IN': ['left', 'right', 'lower', 'upper']}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # acts of DSH
        'name': 'ACT_OF_DSH',
        'pattern': [{'LEMMA': 'act'}, {'LEMMA': 'of'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}},
        'merge': True
    },
    {
        # attempt to DSH
        'name': 'ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # attempt (at) suicide
        'name': 'ATTEMPT_AT_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try']}}, {'LEMMA': 'at', 'OP': '?'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH', 'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # attempt to commit suicide
        'name': 'ATTEMPT_TO_COMMIT_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try', 'attempting', 'trying']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH', 'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # attempt to electrocute herself
        'name': 'ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try', 'attempting', 'trying']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH'}},
        'merge': True
    },
    {
        # voices telling her to kill herself
        'name': 'TELL_TO_ATTEMPT_TO_DSH_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['command', 'compell', 'incite', 'say', 'tell', 'urge']}}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': 'her'}, {'LEMMA': 'to'}, {'POS': 'VERB', 'OP': '?'}, {'POS': 'CCONJ', 'OP': '?'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING', 'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # voices telling her to jump out the window
        'name': 'TELL_TO_ATTEMPT_TO_DSH',
        'pattern': [{'LEMMA': {'IN': ['command', 'compell', 'incite', 'say', 'tell', 'urge']}}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': 'her'}, {'LEMMA': 'to'}, {'POS': 'VERB', 'OP': '?'}, {'POS': 'CCONJ', 'OP': '?'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
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
        'pattern': [{'LEMMA': 'make'}, {'POS': {'IN': ['ADJ', 'DET', 'NUM']}}, {'POS': {'IN': ['ADJ', 'ADV']}, 'OP': '*'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': 'DSH', 'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # DSH behaviour
        'name': 'DSH_BEHAVIOUR',
        'pattern': [{'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': {'IN': ['act', 'action', 'attempt', 'behaviour', 'gesture']}}],
        'avm': {'ALL': {'DSH': 'DSH'}},
        'merge': True
    },
     # DSH NON-RELEVANT
    {
        # thought of self-harm
        'name': 'THOUGHT_OF_DSH',
        'pattern': [{'LEMMA': {'IN': ['dream', 'plan', 'thought']}}, {'LEMMA': {'IN': ['about', 'of']}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # plan to self-harm
        'name': 'PLAN_TO_DSH',
        'pattern': [{'_': {'LA': 'INTENT'}}, {'POS': 'ADVP'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # plan to end her life
        'name': 'PLAN_TO_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['intend', 'intent', 'plan']}}, {'LEMMA': 'to'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {0: {'DSH': False}, 'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # thought of self-harm or suicide
        'name': 'THOUGHT_OF_DSH_OR_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['dream', 'thought']}}, {'LEMMA': {'IN': ['about', 'of']}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}, {'POS': 'CCONJ'}, {'LEMMA': 'suicide'}],
        'avm': {0: {'DSH': False}, 'LAST': {'DSH': 'DSH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # harmful thoughts
        'name': 'HARMFUL_THOUGHT',
        'pattern': [{'LEMMA': 'harmful'}, {'LEMMA': 'thought'}],
        'avm': {'ALL': {'DSH': 'DSH', 'HEDGING': 'HEDGING', 'DSH_TYPE': 'SELF-HARM'}},
        'merge': True
    },
     # DSH NON-RELEVANT
    {
        # suicidal or self-harm ideation
        'name': 'SUICIDAL_CCONJ_DSH_IDEATION',
        'pattern': [{'LEMMA': {'IN': ['suicidal', 'suicide']}}, {'POS': 'CCONJ'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': 'ideation'}],
        'avm': {0: {'DSH': 'DSH', 'HEDGING': 'HEDGING', 'DSH_TYPE': 'SUICIDALITY'}, 'LAST': {'HEDGING': 'HEDGING', 'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # prevent harm to self
        'name': 'AVOID_DSH',
        'pattern': [{'LEMMA': {'IN': ['avoid', 'avert', 'prevent', 'stop']}}, {'OP': '?'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # a way of harming herself
        'name': 'WAY_OF_DSH',
        'pattern': [{'LEMMA': {'IN': ['mean', 'method', 'way']}}, {'LEMMA': 'of'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    # NON-DSH
    {
        # DSH:
        'name': 'DSH_HEADING',
        'pattern': [{'_': {'DSH': 'DSH'}, 'OP': '+'}, {'LEMMA': ':'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # Risk (overdose, self-harm, jumping from height, etc.):
        'name': 'DSH_HEADING_2',
        'pattern': [{'LEMMA': '('}, {'LEMMA': {'NOT_IN': ['(', ')']}, 'TAG': {'NOT_IN': ['VB', 'VBD' 'VBN', 'VBP', 'VBZ']}, 'OP': '+'}, {'LEMMA': ')'}, {'LEMMA': ':'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # mg OD
        'name': 'OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^(mc?gr?s?|(micro|mill?i)?g(ram(me)?)?s?|tablet|tabs?)$'}}, {'LEMMA': {'IN' : ['od', 'OD']}}],
        'avm': {1: {'DSH': False}},
        'merge': True
    },
    {
        # mg OD
        'name': 'NUMUNIT_OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^[0-9\.,]+(mc?gs?|(micro|mill?i)?gram(me)?)$'}}, {'LEMMA': {'IN' : ['od', 'OD']}}],
        'avm': {1: {'DSH': False}},
        'merge': True
    },
    {
        # cut down
        'name': 'CUT_DOWN',
        'pattern': [{'LEMMA': {'IN': ['cut', 'cutting']}}, {'LEMMA': 'down'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # pick up
        'name': 'PICK_UP',
        'pattern': [{'LEMMA': {'IN': ['pick', 'picking']}}, {'LEMMA': 'up'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # scared
        'name': 'SCARED',
        'pattern': [{'ORTH': 'scared'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # cleared from overdose
        'name': 'CLEARED_FROM_DSH',
        'pattern': [{'LEMMA': 'clear'}, {'LEMMA': 'from'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # interpreted as self-harm
        'name': 'INTERPRET_AS_DSH',
        'pattern': [{'LEMMA': {'IN': ['appear', 'interpret', 'look', 'seem']}}, {}, {'LEMMA': 'be', 'OP': '?'}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    {
        # rather than an actual attempt to end her life
        'name': 'RATHER_THAN_DSH',
        'pattern': [{'LEMMA': {'IN': ['rather', 'oppose']}}, {'POS': {'NOT_IN': ['VERB']}, 'OP': '+'},  {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH': False}},
        'merge': True
    },
    # Form elements
    {
        # a) self-harm
        'name': 'BULLET_DSH',
        'pattern': [{'_': {'LA': 'BULLET'}}, {'_': {'DSH': 'DSH'}, 'OP': '+'}],
        'avm': {'ALL': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # a) suicide attempts
        'name': 'BULLET_SUICIDE',
        'pattern': [{'_': {'LA': 'BULLET'}}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'ALL': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # DSH_TYPE: SELF-HARM
        'name': 'DSH_TYPE_SELF-HARM',
        'pattern': [{'_': {'HA_TYPE': 'SELF-HARM'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'SELF-HARM'}},
        'merge': True
    },
    {
        # DSH_TYPE: HITTING
        'name': 'DSH_TYPE_SELF-HITTING',
        'pattern': [{'_': {'HA_TYPE': 'HITTING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'HITTING'}},
        'merge': True
    },
    {
        # DSH_TYPE: OVERDOSE
        'name': 'DSH_TYPE_OVERDOSE',
        'pattern': [{'_': {'HA_TYPE': 'OVERDOSE'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'OVERDOSE'}},
        'merge': True
    },
    {
        # DSH_TYPE: SUICIDALITY
        'name': 'DSH_TYPE_SUICIDALITY',
        'pattern': [{'_': {'HA_TYPE': 'SUICIDALITY'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # DSH_TYPE: CUTTING
        'name': 'DSH_TYPE_SELF-CUTTING',
        'pattern': [{'_': {'HA_TYPE': 'CUTTING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'CUTTING'}},
        'merge': True
    },
    {
        # DSH_TYPE: STRANGULATION
        'name': 'DSH_TYPE_STRANGULATION',
        'pattern': [{'_': {'HA_TYPE': 'STRANGULATION'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'STRANGULATION'}},
        'merge': True
    },
    {
        # DSH_TYPE: SELF-BURNING
        'name': 'DSH_TYPE_BURNING',
        'pattern': [{'_': {'HA_TYPE': 'BURNING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'BURNING'}},
        'merge': True
    },
    {
        # DSH_TYPE: BITING
        'name': 'DSH_TYPE_BITING',
        'pattern': [{'_': {'HA_TYPE': 'BITING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'BITING'}},
        'merge': True
    },
    {
        # DSH_TYPE: STABBING
        'name': 'DSH_TYPE_STABBING',
        'pattern': [{'_': {'HA_TYPE': 'STABBING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'STABBING'}},
        'merge': True
    },
    {
        # DSH_TYPE: TRAUMA
        'name': 'DSH_TYPE_TRAUMA',
        'pattern': [{'_': {'HA_TYPE': 'TRAUMA'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'TRAUMA'}},
        'merge': True
    },
    {
        # DSH_TYPE: SKIN-PICKING
        'name': 'DSH_TYPE_SKIN-PICKING',
        'pattern': [{'_': {'HA_TYPE': 'SKIN-PICKING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'SKIN-PICKING'}},
        'merge': True
    },
    {
        # DSH_TYPE: HAIR-PULLING
        'name': 'DSH_TYPE_HAIR-PULLING',
        'pattern': [{'_': {'HA_TYPE': 'HAIR-PULLING'}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'HAIR-PULLING'}},
        'merge': True
    },
    {
        # DSH_TYPE: SELF-HARM as default
        'name': 'DSH_TYPE_DEFAULT',
        'pattern': [{'_': {'DSH': 'DSH', 'DSH_TYPE': False}, 'OP': '+'}],
        'avm': {'ALL': {'DSH_TYPE': 'SELF-HARM'}},
        'merge': True
    }
]