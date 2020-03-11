'''
docomo API
 - Powered by goo
 - Powered by Jetrun
'''

import requests
import json
import yaml


yml_data = yaml.load(open('config/docomo.yml'))
APIKEY = yml_data['key']


def goo(joke):
    ## -----*----- 形態素解析 -----*----- ##
    url = "https://api.apigw.smt.docomo.ne.jp/gooLanguageAnalysis/v1/morph?APIKEY={}".format( APIKEY )
    header = { 'Content-Type': 'application/json' }
    data = { 'sentence': joke }

    res = requests.post(url, headers=header, data=json.dumps(data))

    return res



def jetrun(joke):
    ## -----*----- センシティブチェック -----*----- ##
    url = 'https://api.apigw.smt.docomo.ne.jp/truetext/v1/sensitivecheck?APIKEY={}'.format( APIKEY )
    header = { 'Content-Type': 'application/x-www-form-urlencoded' }
    body = { 'text': joke }

    res = requests.post(url, headers=header, data=body)

    return res


if __name__ == '__main__':
    print(goo('布団が吹っ飛んだ'))
    print(jetrun('布団が吹っ飛んだ'))
