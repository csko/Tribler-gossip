# Written by BitTornado authors
# see LICENSE.txt for license information

connChoices=(
    {'name':'automatic',
     'rate':{'min':0, 'max':5000, 'def': 0},
     'conn':{'min':0, 'max':100,  'def': 0},
     'automatic':1},
    {'name':'unlimited',
     'rate':{'min':0, 'max':5000, 'def': 0, 'div': 50},
     'conn':{'min':4, 'max':100,  'def': 4}},
    {'name':'dialup/isdn',
     'rate':{'min':3,   'max':   8, 'def':  5},
     'conn':{'min':2, 'max':  3, 'def': 2},
     'initiate': 12},
    {'name':'dsl/cable slow',
     'rate':{'min':10,  'max':  48, 'def': 13},
     'conn':{'min':4, 'max': 20, 'def': 4}},
    {'name':'dsl/cable fast',
     'rate':{'min':20,  'max': 100, 'def': 40},
     'conn':{'min':4, 'max': 30, 'def': 6}},
    {'name':'T1',
     'rate':{'min':100, 'max': 300, 'def':150},
     'conn':{'min':4, 'max': 40, 'def':10}},
    {'name':'T3+',
     'rate':{'min':400, 'max':2000, 'def':500},
     'conn':{'min':4, 'max':100, 'def':20}},
    {'name':'seeder',
     'rate':{'min':0, 'max':5000, 'def':0, 'div': 50},
     'conn':{'min':1, 'max':100, 'def':1}},
    {'name':'SUPER-SEED', 'super-seed':1}
     )

connChoiceList = [x['name'] for x in connChoices]
