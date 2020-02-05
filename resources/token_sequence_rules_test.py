from spacy.tokens import Token

#################################
# Custom attribute declarations #
#################################

Token.set_extension('TEST', default=False, force=True)


#################################
# Token sequence rules, Level 0 #
#################################

"""
    Rules to annotate test example (in token_sequence_annotator.py main):
    No signs of self-harm reported by patient, but her mother cut her arm and 
    cut her legs. I will be very very very happy. I have apples and bananas.
"""

TEST_RULES = [
    {
        # self - harm
        'name': 'SELF-HARM',
        'pattern': [{'LEMMA': 'self'}, {'LEMMA': '-'}, {'ORTH': 'harm'}],
        'avm': {'ALL': {'TEST': 'OK'}},
        'merge': False
    },
    {
        # cut her legs
        'name': 'CUT_HER_LEGS',
        'pattern': [{'LEMMA': 'cut'}, {'ORTH': 'her'}, {'ORTH': {'REGEX': '(arm|leg)s?'}}],
        'avm': {'ALL': {'TEST': 'OK'}},
        'merge': False
    },
    {
        # fruit
        'name': 'FRUIT',
        'pattern': [{'LEMMA': {'IN': ['apple', 'banana']}}],
        'avm': {'ALL': {'TEST': 'OK'}},
        'merge': False
    }
]