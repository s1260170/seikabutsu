"""
bot.py
        
難しかったとこ：
日本語で書かれたブログの内容が古いものだったり、情報が見つけられないものがあり大変だった。    
そんなときは英語のリファレンスを読んで理解した。
    herokuの自動再起動
    twitterAPIの引数にオプション

概要：
    ツイートを長時間取得し続けるbotの制作
    
    ツイートを自動で検索し取得させるサービスはある。
    IFTTのような
        何時間に一回みたいな感じでしかできない
        オンタイムで取得したい！！

    herokuを用いて実現させた。
        heroku環境は一日に一回どこかの時間で勝手に再起動する。
        変数を外部ファイルとして保存しているとリセット（herokuにアップロードされたそのもの状態）されるので扱いが面倒
            最後に読み込んだツイートのツイートされた時間
        
    herokuにはHeroku Scheduleと呼ばれる何秒ごとにプログラムを実行させるという機能がある。
    それを10分に設定して120秒ごとにツイートを取得させるようにした。
        プログラム起動                  0秒目
            120秒前までのツイートを取得  |
                120秒休止              |
            120秒前までのツイートを取得  |
                120秒休止              |
            120秒前までのツイートを取得  |
                120秒休止              |
            120秒前までのツイートを取得  |
        プログラム終了                  |
        プログラム起動                  600秒目
            120秒前までのツイートを取得
    
    twitterのAPIの問題
    何度もtwitterのサーバーにアクセスしすぎると弾かれるようになる。
    APIの引数にオプション書いとかないとだめ
        日本語で探してもなかった

Author: Masato Ishio
Date: 2020-10-02
"""
import tweepy
import time
import datetime
import requests
import re
import json
import sys

#テスト用承認キー選択 
#-tでテスト用のキーが使える
args = sys.argv
if args[1] == '-t':
    import configT
    #APIのkey
    consumer_key = configT.api_key
    consumer_secret = configT.secret_key
    access_token = configT.Access_token
    access_token_secret = configT.Access_token_secret
    #webhookのurl
    webhook_url = configT.webhook_url
    webhook_log = configT.webhook_log
    search_words = configT.search_words
    #検索ワード
    my_twitter_account = configT.my_twitter_accout
else:
    import config
    #APIのkey
    consumer_key = config.api_key
    consumer_secret = config.secret_key
    access_token = config.Access_token
    access_token_secret = config.Access_token_secret
    #webhookのurl
    webhook_url = config.webhook_url
    webhook_log = config.webhook_log
    search_words = config.search_words
    #検索ワード
    my_twitter_account = config.my_twitter_accout

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

#ここが重要です。
#wait_on_rate_limit – Whether or not to automatically wait for rate limits to replenish, wait_on_rate_limit_notify – Whether or not to print a notification when Tweepy is waiting for rate limits to replenish
#サーバにアクセスしすぎると怒られるのでこの設定が必要
api = tweepy.API(auth, wait_on_rate_limit_notify=True, wait_on_rate_limit=True)


def push_to_discord(namae, text, at_time):
    main_content = {
        "username": "@" + namae,
        "content": text + "\n" + at_time.strftime("%m/%d %H:%M"),
    }
    requests.post(webhook_url, main_content)

def push_url_to_discord(namae, text):
    main_content = {"username": "@" + namae, "content": text}
    requests.post(webhook_url, main_content)



def push_log(strb):
    main_content = {"username": "log", "content": strb}
    print(main_content)
    requests.post(webhook_log, main_content)


# 最後に読み込んだツイートのツイートされた時間を示す。ここでは120秒前までにした
old_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=-120)

try:
    push_log("start 4 times")
    for i in range(0, 4):
        push_log("start:")
        push_log(old_time)
        push_log(datetime.datetime.utcnow())
        
        #処理が始まる時間
        t1 = time.perf_counter()
        
        #30個のツイートを取り出す
        for tweet in tweepy.Cursor(
            api.search,
            q=search_words,
            tweet_mode="extended",
        ).items(30):
            
            #もし取り出したツイートがすでにあったならばスルー
            if old_time >= tweet.created_at:
                break
            
            #ツイートのテキストを抽出
            text = tweet.full_text
            #ツイートされた時間（utc）を日本時間にする
            created_time = tweet.created_at + datetime.timedelta(hours=9)
            
            #ツイートしたユーザの名前
            name = tweet.user.screen_name
            #もし自分自身がツイートしたものなら除外
            if name == my_twitter_account:
                break
            
            #ログ書き出し
            push_log("pushed_at:")
            push_log(old_time)
            push_log(tweet.created_at)
            push_log("end:")

            #内容を送信
            push_to_discord(name, text, created_time)
            

            #画像や動画等のメディアが含まれていたらそのURLを抽出
            if "media" in tweet.entities:
                for media in tweet.entities["media"]:
                    url = media["media_url_https"]
                    push_url_to_discord(name, url)

        #最後に読み込んだツイートをすすめる
        old_time = old_time + datetime.timedelta(seconds=120)
        
        #処理にかかった時間　=　処理が終わった時間　-　処理が始まった時間
        t2 = time.perf_counter() - t1
        
        #120で一回の処理にしたいので処理にかかった時間分待つ
        time.sleep(120 - t2)
        
        #何回目かの表示
        push_log("end time:")
        push_log(str(i))
    push_log("end 4 times")

except KeyboardInterrupt:
    # Ctrl-C を捕まえた！
    print("interrupted!")
    # なにか特別な後片付けが必要ならここに書く
    sys.exit(0)

