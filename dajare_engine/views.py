from django.shortcuts import render
from django.http.response import JsonResponse
import json
import engine


model = engine.Evaluate(False)


def joke_judge(request):
    ## -----*----- ダジャレかどうか判定 -----*----- ##
    '''
    uri：
        /joke/judge
    method：
        GET
    headers：
        'Content-Type':'application/json'
    query：
        joke: String,
    response：
        {
            is_joke: Boolean
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'status': 'NG'})

    ret = {
        'is_joke': engine.is_joke(params['joke']),
        'status': 'OK'
    }
    return JsonResponse(ret)



def joke_evaluate(request):
    ## -----*----- ダジャレを評価 -----*----- ##
    # 1.0 ~ 5.0で評価する
    '''
    uri：
        /joke/evaluate
    method：
        GET
    headers：
        'Content-Type':'application/json'
    query：
        joke: String,
    response：
        {
            score: Number
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'status': 'NG'})

    ret = {
        'score': model.predict(params['joke']),
        'status': 'OK'
    }
    return JsonResponse(ret)



def joke_reading(request):
    ## -----*----- ダジャレをカタカナ変換 -----*----- ##
    '''
    uri：
        /joke/reading
    method：
        GET
    headers：
        'Content-Type':'application/json'
    query：
        joke: String,
    response：
        {
            reading: String
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'status': 'NG'})

    ret = {
        'reading': engine.to_katakana(params['joke']),
        'status': 'OK'
    }
    return JsonResponse(ret)
