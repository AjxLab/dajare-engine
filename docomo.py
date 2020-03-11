'''
docomo API
'''

import requests
import json
import yaml


yml_data = yaml.load(open('config/docomo.yml'))
APIKEY = yml_data['key']
print(APIKEY)

def goo(joke, apikey):
    ## -----*----- Powered by goo -----*----- ##
    # 形態素解析

    url = 'https://api.apigw.smt.docomo.ne.jp/truetext/v1/sensitivecheck?APIKEY={}'.format( APIKEY )
    header = {'Content-Type': 'application/x-www-form-urlencoded'}
    body = { "text": joke }

    response = requests.post(url, headers=header, data=body)

