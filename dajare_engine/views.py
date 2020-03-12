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
            is_joke: Boolean,
            include_sensitive: Boolean,
            status: String,
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'is_joke': None, 'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'is_joke': None, 'status': 'NG'})

    if not params['joke']=='':
        # ダジャレ判定
        is_joke = engine.is_joke(params['joke'])

        # センシティブな情報が含まれているか
        include_sensitive = False
        res = engine.docomo.jetrun(params['joke'])
        if engine.docomo.check_health(res):
            if 'quotients' in res.json():
                include_sensitive = True
    else:
        is_joke = False
        include_sensitive = False

    ret = {
        'is_joke': is_joke,
        'include_sensitive': include_sensitive,
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
            score: Number,
            status: String,
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'score': None, 'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'score': None, 'status': 'NG'})

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
            reading: String,
            status: String,
        }
    '''

    # パラメータを辞書で取得
    params = request.GET

    # GET以外でアクセス -> return {}
    if request.method != 'GET':
        return JsonResponse({'reading': None, 'status': 'NG'})
    # クエリを指定されていない -> return {}
    if not 'joke' in params:
        return JsonResponse({'reading': None, 'status': 'NG'})

    ret = {
        'reading': engine.to_katakana(params['joke']),
        'status': 'OK'
    }
    return JsonResponse(ret)
