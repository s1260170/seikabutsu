"""
tweets_analysis.py

概要：
    ツイートから性格を分析することができるソフト
    BIG５のグラフを表示させることができる        

感想：
    APIで帰ってくるものがjsonでそれをどう扱うかを勉強することができた
    そもそもAPIつかったのこれがはじめてかもししれない
    マットプロットリブでグラフを表示させることができた
    jsonからグラフにどう変形させるのかみたいなことも勉強できたので良かった

    ただツイートを取得してibmのサーバーに投げて帰ってきたものをグラフに整形してるだけで動作は単純

Author: Masato Ishio
Date: 2020-10-02
"""





import json
import matplotlib.pyplot as plt
import numpy as np
from math import pi
import tweepy
import re
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import sys
from tqdm import tqdm

args = sys.argv
if args[1] == '-t':
    import configT
    consumer_key = configT.api_key
    consumer_secret = configT.secret_key
    access_token = configT.Access_token
    access_token_secret = configT.Access_token_secret
    bearer_token = configT.bmi_bearer_token
else:
    import config
    #APIのkey
    consumer_key = config.api_key
    consumer_secret = config.secret_key
    access_token = config.Access_token
    access_token_secret = config.Access_token_secret
    bearer_token = config.bmi_bearer_token


num = 0
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# APIインスタンスを生成
authenticator = IAMAuthenticator(bearer_token)
personality_insights = PersonalityInsightsV3(
    version="2017-10-13", authenticator=authenticator
)
personality_insights.set_service_url(
    "https://api.jp-tok.personality-insights.watson.cloud.ibm.com"
)

for k in range(0, 5):
    for j in range(0, 5):
        name = input("調べたいユーザのIDを入力してください: @")
        with open("./temp.txt", "w", encoding="utf-8") as f:
            print("ツイートを取得中です")
            for page in tqdm(range(1, 17)):
                try:
                    user_tweets = api.user_timeline(name, count=200, page=page)
                    b = True
                except:
                    print("エラーが発生しました。")
                    print(sys.exc_info())
                    b = False
                    break
                for getted_tweets in user_tweets:
                    getted_tweets_text = getted_tweets.text
                    # public_tweets = api.home_timeline()
                    # RTを削除
                    if "RT" in getted_tweets_text:
                        continue
                    # ツイートから，URLとリプライ先のユーザIDを削除
                    # URLの正規表現
                    # rはstring
                    # getted_tweets_text = re.sub(r"RT", "", getted_tweets_text)
                    # getted_tweets_text = re.sub(
                    #    r"@[A-Za-z0-9_]+: ", "", getted_tweets_text
                    # )
                    getted_tweets_text = re.sub(
                        r"(https?|ftp)(:\/\/[-_\.!~*\'()a-zA-Z0-9;\/?:\@&=\+\$,%#]+)",
                        "",
                        getted_tweets_text,
                    )
                    getted_tweets_text = re.sub(
                        r"@[A-Za-z0-9_]+ ", "", getted_tweets_text
                    )
                    # @(a-zかA-Zか0－9か_が1回以上)
                    # ハッシュタグを削除
                    getted_tweets_text = re.sub(
                        r"#[一-龥々ぁ-んァ-ンA-ZＡ-Ｚa-zａ-ｚ0-9０-９_]+", "", getted_tweets_text
                    )
                    getted_tweets_text = re.sub(r"[\n\n]+", "", getted_tweets_text)
                    num += 1
                    f.write(getted_tweets_text + "\n")
        if b == True:
            break
    print("\n@" + name + "さんの" + str(num) + "ツイートを読み込みました")
    # 性格を分析
    with open("./temp.txt", "r", encoding="utf-8") as profile_text:
        try:
            profile = personality_insights.profile(
                profile_text.read(),
                "application/json",
                content_language="ja",
                accept_language="ja",
                consumption_preferences=True,
                raw_scores=True,
            ).get_result()
            # ファイルに書き込み
            with open("./result.json", "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
                break
        except:
            print(sys.exc_info())


bigfive_dicts = {}
# bigfiveの辞書
consumption_preferences_dicts = {}
# 生活の傾向
needs_dicts = {}
# 　商品側面の概要
with open("./result.json", "r", encoding="utf-8") as f:
    mydict = json.load(f)

    for pre_bigfive_dict in mydict["personality"]:
        bigfive_dicts[pre_bigfive_dict["name"]] = pre_bigfive_dict["percentile"]

    for consumption_preference_category in mydict["consumption_preferences"]:
        for pre_consumption_preferences_dict in consumption_preference_category[
            "consumption_preferences"
        ]:
            if pre_consumption_preferences_dict["score"] == 1.0:
                consumption_preferences_dicts.setdefault(
                    consumption_preference_category["name"], []
                ).append(pre_consumption_preferences_dict["name"])
            # https://qiita.com/tag1216/items/b2765e9e87025c01e57f

    for pre_need in mydict["needs"]:
        if pre_need["percentile"] >= 0.5:
            needs_dicts[pre_need["name"]] = pre_need["percentile"]
            # https://cloud.ibm.com/docs/personality-insights?topic=personality-insights-needs&locale=ja


# Set data
cat = [
    "Openness",
    "Conscientiousness",
    "Extraversion",
    "Agreeableness",
    "Emotional_range",
]

values = list(map(lambda x: x * 100, bigfive_dicts.values()))
N = len(cat)

x_as = [n / float(N) * 2 * pi for n in range(N)]

# Because our chart will be circular we need to append a copy of the first
# value of each list at the end of each list with data
values += values[:1]
x_as += x_as[:1]


# Set color of axes
plt.rc("axes", linewidth=0.5, edgecolor="#888888")


# Create polar plot
ax = plt.subplot(111, polar=True)


# Set clockwise rotation. That is:
ax.set_theta_offset(pi / 2)
ax.set_theta_direction(-1)


# Set position of y-labels
ax.set_rlabel_position(0)


# Set color and linestyle of grid
ax.xaxis.grid(True, color="#888888", linestyle="solid", linewidth=0.5)
ax.yaxis.grid(True, color="#888888", linestyle="solid", linewidth=0.5)


# Set number of radial axes and remove labels
plt.xticks(x_as[:-1], [])
# Set yticks
plt.yticks([25, 50, 75, 100], ["25", "ave", "75", "100"])
# Plot data
ax.plot(x_as, values, linewidth=0, linestyle="solid", zorder=3)
# Fill area
ax.fill(x_as, values, "b", alpha=0.3)
# Set axes limits
plt.ylim(0, 100)


# Draw ytick labels to make sure they fit properly
for i in range(N):
    angle_rad = i / float(N) * 2 * pi

    if angle_rad == 0:
        ha, distance_ax = "center", 10
    elif 0 < angle_rad < pi:
        ha, distance_ax = "left", 1
    elif angle_rad == pi:
        ha, distance_ax = "center", 1
    else:
        ha, distance_ax = "right", 1

    ax.text(
        angle_rad,
        100 + distance_ax,
        cat[i],
        size=10,
        horizontalalignment=ha,
        verticalalignment="center",
    )

needs_dicts = dict(sorted(needs_dicts.items(), key=lambda x: x[1], reverse=True))


print(
    "\n<@"
    + name
    + "さんのBigFive>++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
)
rank = 0
# for dict in bigfive_dicts:
for k, v in bigfive_dicts.items():
    rank = 100 - round((v * 100))
    print(str(k) + "は100人中" + str(rank) + "番目に位置しています。", end="")
    if rank > 50:
        print("平均以下です！！！！！。")
    else:
        print("")
    # https://note.nkmk.me/python-dict-keys-values-items/
i = 0
print("\n<@" + name + "さんが共感を感じる言葉>++++++++++++++++++++++++++++++++++++++++++++++++")
for k in needs_dicts.keys():
    print(k)
    i += 1
    if i == 5:
        break
print(
    "\n<@"
    + name
    + "さんの消費嗜好性>++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
)
for k, v in consumption_preferences_dicts.items():
    for ls in v:
        print(ls)
# print(consumption_preferences_dicts)
# Show polar plot
print("\n")
print("何か入力すると終了します")
plt.show()
input()

sys.exit()
