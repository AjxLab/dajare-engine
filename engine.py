#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, re
import numpy as np
from tensorflow.keras import *
from tensorflow.keras.layers import *
from tensorflow.keras.callbacks import *
from tensorflow.keras.optimizers import *
from tensorflow.keras.models import *
from tensorflow.keras import Sequential
from janome.tokenizer import Tokenizer
from kanjize import int2kanji
import jaconv
import pyboin
from tqdm import tqdm
import json
import math
import statistics
import docomo


class Evaluate(object):
    '''
    ダジャレを評価するモデル
    character-level CNNを用いて評価
    '''

    def __init__(self, train=True, model_path='model/model.hdf5'):
        # -----*----- コンストラクタ -----*----- ##
        # TensorFlowの警告レベルを設定
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        # モデルのビルド
        self.__model = self.__build()

        self.model_path = model_path

        if train:
            # 学習
            x, y = self.__features_extracter()
            self.__train(x, y)
        else:
            # モデルの読み込み
            self.load_model()


    def __build(self, embed_size=128, max_length=100, filter_sizes=(2, 3, 4, 5), filter_num=64, learning_rate=0.0005):
        ## -----*----- モデルをビルド -----*----- ##
        # Input Layer
        input_ts = Input(shape=(max_length, ))
        # Embedding 各文字をベクトル変換
        emb = Embedding(0xffff, embed_size)(input_ts)
        emb_ex = Reshape((max_length, embed_size, 1))(emb)
        # 各カーネルサイズで畳み込みをかける．

        convs = []
        # Conv2D
        for filter_size in filter_sizes:
            conv = Conv2D(filter_num, (filter_size, embed_size), activation='relu')(emb_ex)
            pool = MaxPooling2D((max_length - filter_size + 1 , 1))(conv)
            convs.append(pool)
        # ConcatenateでConv2Dを結合
        convs_merged = Concatenate()(convs)
        # Reshape
        reshape = Reshape((filter_num * len(filter_sizes),))(convs_merged)
        # Dense
        fc1 = Dense(64, activation='relu')(reshape)
        bn1 = BatchNormalization()(fc1)
        do1 = Dropout(0.5)(bn1)
        #fc2 = Dense(1, activation='sigmoid')(do1)
        fc2 = Dense(5, activation='softmax')(do1)

        # Model generate
        model = Model(
            inputs=[input_ts],
            outputs=[fc2]
        )

        # モデルをコンパイル
        model.compile(
            optimizer=Adam(lr=learning_rate),
            #loss='binary_crossentropy',
            loss='sparse_categorical_crossentropy',
            metrics=["accuracy"]
        )

        return model


    def __train(self, x, y, batch_size=1000, epoch_count=50, max_length=30):
        ## -----*----- 学習 -----*----- ##
        self.__model.fit(
            x, y,
            nb_epoch=epoch_count,
            batch_size=batch_size,
            verbose=1,
            validation_split=0.2,
            shuffle=True,
        )

        # 最終の学習モデルを保存
        self.__model.save_weights(self.model_path)


    def __features_extracter(self, max_length=100):
        ## -----*----- 特徴量抽出 -----*----- ##
        x = [] # 入力
        y = [] # 正解ラベル

        # ダジャレ読み込み
        jokes = []
        jokes = json.load(open('data/jokes.json', 'r'))

        # 正規化
        print('Normalizing...')
        while True:
            for i in range(len(jokes)):
                jokes[i]['score'] += np.random.rand() - 0.5

            ave = statistics.mean([j['score'] for j in jokes])
            dev = statistics.pstdev([j['score'] for j in jokes])

            for i in range(len(jokes)):
                jokes[i]['score'] = 3 + (jokes[i]['score'] - ave) / dev

            map_score = np.zeros(5)
            for j in jokes:
                if j['score'] < 1.0:  j['score'] = 1.0
                if j['score'] > 5.0:  j['score'] = 5.0
                map_score[int(np.round(j['score']))-1] += 1

            flag = True
            for col in 100 * map_score / len(jokes) /  np.array([7, 25, 36, 25, 7]):
                if abs(1.0-col) > 0.1:
                    flag = False
            if flag:  break

        # データセットを作成
        for joke in tqdm(jokes):
            katakana = to_katakana(joke['joke'])[0]
            vec = [ord(x) for x in katakana]
            vec = vec[:max_length]
            if len(vec) < max_length:
                vec += ([0] * (max_length - len(vec)))

            score = int(np.round(joke['score'])) - 1
            if score < 0: score = 0
            if score > 4: score = 4

            x.append(vec)
            y.append(score)

        x = np.array(x)
        y = np.array(y)

        return x, y


    def load_model(self):
        ## -----*----- モデル読み込み -----*----- ##
        # モデルが存在する場合に読み込む
        if os.path.exists(self.model_path):
            self.__model.load_weights(self.model_path)


    def predict(self, sentence, max_length=100):
        ## -----*----- 推論 -----*----- ##
        katakana = to_katakana(sentence)[0]
        vec = [ord(x) for x in katakana]
        vec = vec[:max_length]
        if len(vec) < max_length:
            vec += ([0] * (max_length - len(vec)))

        pred = self.__model.predict(np.array([vec]))[0]
        bias = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        bias[np.argmax(pred)] = 0.0
        bias = np.sum(pred * bias) * 10.0
        pred *= np.array([8.4, 0.7, 0.12, 2.3, 0.8])

        score = np.argmax(pred) + bias + 1.0

        while score < 1.0 or score > 5.0:
            if score < 1.0:
                score += abs(bias*0.313)
            if score > 5.0:
                score -= abs(bias*0.313)

        return score


t = Tokenizer()


def to_katakana(sentence, use_api=True):
    ## -----*----- カタカナ変換 -----*----- ##
    '''
    sentence：判定対象の文
    '''
    katakana = ''

    # APIを利用
    if use_api:
        res = docomo.goo(sentence)
        if docomo.check_health(res):
            # APIが利用可
            katakana = res.json()['converted'].replace(' ', '')
    # APIを利用しない || APIが利用不可
    if katakana == '':
        # APIが利用不可
        # 数字 -> 漢数字
        for c in re.findall('\d+', sentence):
            sentence = sentence.replace(c, int2kanji(int(c)))

        # 形態素解析
        for token in t.tokenize(sentence):
            reading = token.reading

            if reading == '*':
                # 読みがわからないトークン
                katakana += jaconv.hira2kata(token.surface)
            else:
                # 読みがわかるトークン
                katakana += reading

    # ２文字以上の形態素を抽出
    morphemes = []
    for token in t.tokenize(sentence):
        if len(token.reading) >= 2:
            morphemes.append(token.reading)

    # 強制的にカタカナ化
    katakana = jaconv.hira2kata(katakana)
    # 「ッ」を削除
    katakana_rm_ltu = katakana.replace('ッ', '')
    # カタカナのみ抽出
    katakana = ''.join(re.findall('[ァ-ヴー]+', katakana))
    katakana_rm_ltu= ''.join(re.findall('[ァ-ヴー]+', katakana_rm_ltu))

    return katakana, katakana_rm_ltu, morphemes


def judge_joke(katakana, morphemes, n=3):
    ## -----*----- 判定 -----*----- ##
    # Trigram
    col = n_gram(katakana, n)

    # 形態素と同じ音が出現
    for morpheme in morphemes:
        if katakana.count(morpheme) >= 2:
            return True

    if len(set(col)) != len(col):
        return True
    else:
        for i in range(len(col)):
            for j in range(len(col)):
                if i==j:  continue
                # 2文字被り && 母音完全一致
                if num_of_matching(col[i], col[j]) == 2 and pyboin.text2boin(col[i]) == pyboin.text2boin(col[j]):
                    return True

        return False


def num_of_matching(s1, s2):
    ## -----*----- 文字列の一致数 -----*----- ##
    num = 0
    for i in range(len(s1)):
        if s1[i] == s2[i]:
            num += 1

    return num


def hyphen_to_vowel(katakana):
    ## -----*----- 'ー'を母音に変換 -----*----- ##
    ret = ''
    for i in range(len(katakana)):
        if katakana[i] != 'ー':
            ret += katakana[i]
            continue
        if i==0 and katakana[0]!='ー':
            ret += katakana[0]
            continue

        # 直前文字の母音を求める
        ret += pyboin.text2boin(katakana[i-1])

    return ret


def boin_convert(katakana):
    ## -----*----- 母音を変換 -----*----- ##
    for col in n_gram(katakana, 2):
        # 「ou」 -> 「oー」
        if pyboin.text2boin(col) == 'オウ':
            katakana = katakana.replace(col, col.replace('ウ', 'ー'))
        # 「ei」 -> 「eー」
        elif pyboin.text2boin(col) == 'エイ':
            katakana = katakana.replace(col, col.replace('イ', 'ー'))

    return katakana


def n_gram(target, n):
    ## -----*----- n-gram -----*----- ##
    return [ target[idx:idx + n] for idx in range(len(target) - n + 1) ]


def is_joke(sentence, first=True, morphemes=[]):
    ## -----*----- ダジャレ判定 -----*----- ##
    '''
    sentence：判定対象の文
    first：１回目の検証かどうか
    '''
    if first:
        # 3文字以上連続した文字をユニーク化
        tmp = ''
        for c in sentence:
            if len(tmp) < 2:
                tmp += c
            elif tmp[-1]==tmp[-2] and tmp[-1]==c:
                continue
            else:
                tmp += c
        sentence = tmp

        # カタカナ変換
        katakana, katakana_rm_ltu, morphemes = to_katakana(sentence)

        # 空文字の場合 -> False
        if katakana == '':
            return False

        # 母音が連続 -> 「母音ー」とする
        for i in range(len(katakana)-1):
            if not katakana[i+1] in 'アイウエオ':
                continue
            if pyboin.text2boin(katakana[i]) == pyboin.text2boin(katakana[i+1]):
                katakana = katakana[:i+1] + 'ー' + katakana[i+2:]

        # 文字置換
        pair = [
            'ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヂガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ',
            'アイウエオツヤユヨワアイウエオツヤユヨワジカキクケコサシスセソタチツテトハヒフヘホハヒフヘホ'
        ]
        for i in range(len(pair[0])):
            katakana = katakana.replace(pair[0][i], pair[1][i])
            katakana_rm_ltu = katakana_rm_ltu.replace(pair[0][i], pair[1][i])
            for j, morpheme in enumerate(morphemes):
                morphemes[j] = morpheme.replace(pair[0][i], pair[1][i])

    else:
        katakana = boin_convert(sentence)
        katakana_rm_ltu = katakana

    if judge_joke(katakana, morphemes):
        return True
    else:
        if 'ー' in katakana:
            # 'ー'を削除
            if is_joke(katakana.replace('ー', ''), first=False, morphemes=morphemes):
                return True
            # 'ー'を直前文字の母音に変換
            if is_joke(hyphen_to_vowel(katakana), first=False, morphemes=morphemes):
                return True

        if first and ('ッ' in sentence or 'っ' in sentence):
            # 'っ'を削除
            if is_joke(katakana_rm_ltu, first=False, morphemes=morphemes):
                return True

    return False


if __name__ == '__main__':
    jokes = []
    jokes.append('布団が吹っ飛んだ')
    jokes.append('紅茶が凍っちゃった')
    jokes.append('芸無なゲーム')
    jokes.append('Gmailで爺滅入る')
    jokes.append('つくねがくっつくね')
    jokes.append('ソースを読んで納得したプログラマ「そーすね」')
    jokes.append('太古の太閤が太鼓で対抗')
    jokes.append('スロットで金すろーと')
    jokes.append('ニューヨークで入浴')

    model = Evaluate(False)

    for joke in jokes:
        score = model.predict(joke)
        star =  '★' * int(np.round(score))
        star += '☆' * (5-len(star))
        judge = is_joke(joke)

        print('{}\n    - ダジャレ判定：{}'.format(joke, judge))
        if judge:
            print('    - ダジャレ評価：{} ({})'.format(star, score))
        else:
            print('    - カタカナ変換：%s' % to_katakana(joke)[0])

