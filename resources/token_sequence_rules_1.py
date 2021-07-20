#################################
# Token sequence rules, Level 1 #
#################################

# NB rules that use custom attributes added in previous rules go here and are applied in a second application


RULES_1 = [
    {
        # SH and BODY_PART (for coordinated body parts)
        'name': 'SH_AND_BODY_PART',
        'pattern': [{'_': {'SH': 'SH'}}, {'LEMMA': 'and'}, {'LEMMA': {'IN': ['all', 'both']}, 'OP': '?'}, {'LEMMA': {'IN': ['her', 'his', 'their']}, 'OP': '?'}, {'LEMMA': {'IN': ['left', 'right', 'lower', 'upper']}, 'OP': '*'}, {'_': {'LA': 'BODY_PART'}}],
        'avm': {'ALL': {'SH': 'SH'}},
        'merge': True
    },
    {
        # acts of SH
        'name': 'ACT_OF_SH',
        'pattern': [{'LEMMA': 'act'}, {'LEMMA': 'of'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {0: {'SH': False}},
        'merge': True
    },
    {
        # attempt to SH
        'name': 'ATTEMPT_TO_SH',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'bid', 'try']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH'}},
        'merge': True
    },
    {
        # attempt to kill herself
        'name': 'ATTEMPT_TO_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # want to kill herself
        'name': 'WANT_TO_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['desire', 'want', 'wish']}}, {'LEMMA': 'to'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # attempt (at) suicide
        'name': 'ATTEMPT_AT_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'try']}}, {'LEMMA': 'at', 'OP': '?'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # attempt to commit suicide
        'name': 'ATTEMPT_TO_COMMIT_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'bid', 'try', 'attempting', 'trying']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # attempt to electrocute herself
        'name': 'ATTEMPT_TO_SH',
        'pattern': [{'LEMMA': {'IN': ['attempt', 'bid', 'try', 'attempting', 'trying']}}, {'LEMMA': {'IN': ['at', 'to']}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH'}},
        'merge': True
    },
    {
        # voices telling her to kill herself
        'name': 'TELL_TO_ATTEMPT_TO_SH_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['command', 'compell', 'incite', 'say', 'tell', 'urge']}}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': {'IN': ['her', 'him', 'them']}}, {'LEMMA': 'to'}, {'POS': 'VERB', 'OP': '?'}, {'POS': 'CCONJ', 'OP': '?'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'HEDGING': 'HEDGING', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # voices telling her to jump out the window
        'name': 'TELL_TO_ATTEMPT_TO_SH',
        'pattern': [{'LEMMA': {'IN': ['command', 'compell', 'incite', 'say', 'tell', 'urge']}}, {'LEMMA': 'to', 'OP': '?'}, {'LEMMA': {'IN': ['her', 'him', 'them']}}, {'LEMMA': 'to'}, {'POS': 'VERB', 'OP': '?'}, {'POS': 'CCONJ', 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'SH': 'SH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # cuts from self-harm
        'name': 'HARM_ACTION_N_FROM_SH',
        'pattern': [{'_': {'LA': 'HARM_ACTION'}}, {'LEMMA': 'from'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': 'SH'}},
        'merge': True
    },
    {
        # made a suicide attempt
        'name': 'MAKE_SUICIDE_ATTEMPT',
        'pattern': [{'LEMMA': 'make'}, {'POS': {'IN': ['ADJ', 'DET', 'NUM']}}, {'POS': {'IN': ['ADJ', 'ADV']}, 'OP': '*'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': 'SH', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # SH behaviour
        'name': 'SH_BEHAVIOUR',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'LEMMA': {'IN': ['act', 'action', 'attempt', 'behaviour', 'gesture']}}],
        'avm': {'ALL': {'SH': 'SH'}},
        'merge': True
    },
     # SH NON-RELEVANT
    {
        # thought of self-harm
        'name': 'THOUGHT_OF_SH',
        'pattern': [{'LEMMA': {'IN': ['dream', 'plan', 'thought']}}, {'LEMMA': {'IN': ['about', 'of']}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {0: {'SH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # feel like cutting her throat
        'name': 'FEEL_LIKE_SH',
        'pattern': [{'LEMMA': 'feel'}, {'LEMMA': {'IN': ['like', 'compel', 'force']}}, {'POS': {'IN': ['ADVP', 'TO']}, 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP':'+'}],
        'avm': {'LAST': {'SH': 'SH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # intention to take an overdose
        'name': 'INTENTION_TO_TAKE_AN_OD',
        'pattern': [{'_': {'LA': 'INTENT'}}, {'LEMMA': 'to'}, {'_': {'LA': 'OD'}, 'OP': '+'}],
        'avm': {0: {'SH': False}, 1: {'SH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # plan to self-harm
        'name': 'PLAN_TO_SH',
        'pattern': [{'_': {'LA': 'INTENT'}}, {'POS': {'IN': ['ADVP', 'TO']}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {0: {'SH': False}, 1: {'SH': False}, 'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # plan to end her life
        'name': 'PLAN_TO_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['intend', 'intent', 'plan']}}, {'LEMMA': 'to'}, {'_': {'LA': 'SUICIDE'}, 'OP': '+'}],
        'avm': {0: {'SH': False}, 'LAST': {'SH': 'SH', 'HEDGING': 'HEDGING'}},
        'merge': False
    },
    {
        # thought of self-harm or suicide
        'name': 'THOUGHT_OF_SH_OR_SUICIDE',
        'pattern': [{'LEMMA': {'IN': ['dream', 'thought']}}, {'LEMMA': {'IN': ['about', 'of']}}, {'_': {'SH': 'SH'}, 'OP': '+'}, {'POS': 'CCONJ'}, {'LEMMA': 'suicide'}],
        'avm': {0: {'SH': False}, 'LAST': {'SH': 'SH', 'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # harmful thoughts
        'name': 'HARMFUL_THOUGHT',
        'pattern': [{'LEMMA': 'harmful'}, {'LEMMA': 'thought'}],
        'avm': {'ALL': {'SH': 'SH', 'HEDGING': 'HEDGING', 'SH_TYPE': 'SELF-HARM'}},
        'merge': True
    },
     # SH NON-RELEVANT
    {
        # suicidal or self-harm ideation
        'name': 'SUICIDAL_CCONJ_SH_IDEATION',
        'pattern': [{'LEMMA': {'IN': ['suicidal', 'suicide']}}, {'POS': 'CCONJ'}, {'_': {'SH': 'SH'}, 'OP': '+'}, {'LEMMA': 'ideation'}],
        'avm': {0: {'SH': 'SH', 'HEDGING': 'HEDGING', 'SH_TYPE': 'SUICIDALITY'}, 'LAST': {'HEDGING': 'HEDGING', 'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # prevent harm to self
        'name': 'AVOID_SH',
        'pattern': [{'LEMMA': {'IN': ['avoid', 'avert', 'prevent', 'stop']}}, {'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # a way of harming herself
        'name': 'WAY_OF_SH',
        'pattern': [{'LEMMA': {'IN': ['mean', 'method', 'way']}}, {'LEMMA': 'of'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'LAST': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    # NON-SH
    {
        # SH:
        'name': 'SH_HEADING',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'LEMMA': ':'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # accidentally SH
        'name': 'ACCIDENTALLY_SH',
        'pattern': [{'LEMMA': {'IN': ['accidentally', 'unintentionally']}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # SH accidentally
        'name': 'SH_ACCIDENTALLY',
        'pattern': [{'_': {'SH': 'SH'}, 'OP': '+'}, {'LEMMA': {'IN': ['accidentally', 'unintentionally']}}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # Risk (overdose, self-harm, jumping from height, etc.):
        'name': 'SH_HEADING_2',
        'pattern': [{'LEMMA': '('}, {'LEMMA': {'NOT_IN': ['(', ')']}, 'TAG': {'NOT_IN': ['VB', 'VBD' 'VBN', 'VBP', 'VBZ']}, 'OP': '+'}, {'LEMMA': ')'}, {'LEMMA': ':'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # mg OD
        'name': 'OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^(mc?gr?s?|(micro|mill?i)?g(ram(me)?)?s?|tablet|tabs?)$'}}, {'LEMMA': {'IN' : ['od', 'OD']}}],
        'avm': {1: {'SH': False}},
        'merge': True
    },
    {
        # mg OD
        'name': 'NUMUNIT_OD_DOSAGE',
        'pattern': [{'LEMMA': {'REGEX': '^[0-9\.,]+(mc?gs?|(micro|mill?i)?gram(me)?)$'}}, {'LEMMA': {'IN' : ['od', 'OD']}}],
        'avm': {1: {'SH': False}},
        'merge': True
    },
    {
        # OD AM
        'name': 'OD_AM_DOSAGE',
        'pattern': [{'LEMMA': {'IN' : ['od', 'OD', 'o.d.', 'o.d']}}, {'LEMMA': {'IN' : ['am', 'AM', 'a.m.', 'a.m', 'pm', 'PM', 'p.m.', 'p.m']}}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # cut down
        'name': 'CUT_DOWN',
        'pattern': [{'LEMMA': {'IN': ['cut', 'cutting']}}, {'LEMMA': 'down'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # pick up
        'name': 'PICK_UP',
        'pattern': [{'LEMMA': {'IN': ['pick', 'picking']}}, {'LEMMA': {'REGEX': '(her|him|them)sel(f|ves)'}, 'OP': '?'}, {'LEMMA': 'up'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # scared
        'name': 'SCARED',
        'pattern': [{'ORTH': 'scared'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # cleared from overdose
        'name': 'CLEARED_FROM_SH',
        'pattern': [{'LEMMA': 'clear'}, {'LEMMA': 'from'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # interpreted as self-harm
        'name': 'INTERPRET_AS_SH',
        'pattern': [{'LEMMA': {'IN': ['appear', 'interpret', 'look', 'seem']}}, {}, {'LEMMA': 'be', 'OP': '?'}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    {
        # rather than an actual attempt to end her life
        'name': 'RATHER_THAN_SH',
        'pattern': [{'LEMMA': {'IN': ['rather', 'oppose']}}, {'POS': {'NOT_IN': ['VERB']}, 'OP': '+'},  {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'SH': False}},
        'merge': True
    },
    # Form elements
    {
        # a) self-harm
        'name': 'BULLET_SH',
        'pattern': [{'_': {'LA': 'BULLET'}}, {'_': {'SH': 'SH'}, 'OP': '+'}],
        'avm': {'ALL': {'HEDGING': 'HEDGING'}},
        'merge': True
    },
    {
        # Self-harm -
        'name': 'SH_SENTSTART_PUNCT',
        'pattern': [{'_': {'SH': 'SH'}, 'IS_SENT_START': True}, {'LEMMA': {'IN': ['-', ':']}}],
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
        # SH_TYPE: SELF-HARM
        'name': 'SH_TYPE_SELF-HARM',
        'pattern': [{'_': {'HA_TYPE': 'SELF-HARM'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'SELF-HARM'}},
        'merge': True
    },
    {
        # SH_TYPE: HITTING
        'name': 'SH_TYPE_SELF-HITTING',
        'pattern': [{'_': {'HA_TYPE': 'HITTING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'HITTING'}},
        'merge': True
    },
    {
        # SH_TYPE: OVERDOSE
        'name': 'SH_TYPE_OVERDOSE',
        'pattern': [{'_': {'HA_TYPE': 'OVERDOSE'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'OVERDOSE'}},
        'merge': True
    },
    {
        # SH_TYPE: SUICIDALITY
        'name': 'SH_TYPE_SUICIDALITY',
        'pattern': [{'_': {'HA_TYPE': 'SUICIDALITY'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'SUICIDALITY'}},
        'merge': True
    },
    {
        # SH_TYPE: CUTTING
        'name': 'SH_TYPE_SELF-CUTTING',
        'pattern': [{'_': {'HA_TYPE': 'CUTTING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'CUTTING'}},
        'merge': True
    },
    {
        # SH_TYPE: STRANGULATION
        'name': 'SH_TYPE_STRANGULATION',
        'pattern': [{'_': {'HA_TYPE': 'STRANGULATION'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'STRANGULATION'}},
        'merge': True
    },
    {
        # SH_TYPE: SELF-BURNING
        'name': 'SH_TYPE_BURNING',
        'pattern': [{'_': {'HA_TYPE': 'BURNING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'BURNING'}},
        'merge': True
    },
    {
        # SH_TYPE: BITING
        'name': 'SH_TYPE_BITING',
        'pattern': [{'_': {'HA_TYPE': 'BITING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'BITING'}},
        'merge': True
    },
    {
        # SH_TYPE: STABBING
        'name': 'SH_TYPE_STABBING',
        'pattern': [{'_': {'HA_TYPE': 'STABBING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'STABBING'}},
        'merge': True
    },
    {
        # SH_TYPE: TRAUMA
        'name': 'SH_TYPE_TRAUMA',
        'pattern': [{'_': {'HA_TYPE': 'TRAUMA'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'TRAUMA'}},
        'merge': True
    },
    {
        # SH_TYPE: SKIN-PICKING
        'name': 'SH_TYPE_SKIN-PICKING',
        'pattern': [{'_': {'HA_TYPE': 'SKIN-PICKING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'SKIN-PICKING'}},
        'merge': True
    },
    {
        # SH_TYPE: HAIR-PULLING
        'name': 'SH_TYPE_HAIR-PULLING',
        'pattern': [{'_': {'HA_TYPE': 'HAIR-PULLING'}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'HAIR-PULLING'}},
        'merge': True
    },
    {
        # SH_TYPE: SELF-HARM as default
        'name': 'SH_TYPE_DEFAULT',
        'pattern': [{'_': {'SH': 'SH', 'SH_TYPE': False}, 'OP': '+'}],
        'avm': {'ALL': {'SH_TYPE': 'SELF-HARM'}},
        'merge': True
    }
]