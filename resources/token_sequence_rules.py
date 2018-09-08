RULES = [
    {
        'name': 'CUT_HER_X_ARM',
        'pattern': [{'LOWER': 'cut'}, {'LOWER': 'her'}, {'REGEX': '^(arms?|hands?|legs?)'}],
        'avm': {0: {'DSH': 'TRUE'}, 1: {'DSH': 'TRUE'}, 2: {'DSH': 'TRUE'}}
    }
]