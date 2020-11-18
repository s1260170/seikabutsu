"""
kickbot.py
        
感想：
こんなに長いコードになってしまった
大変

概要：
    dicordにてサブスクリプションサービスを提供できるようになるBOT
        制限した人数を超えて入ってきた人がいると、もといるメンバーがランダムに自動でキックされる。
        課金ユーザは有効期限が設定され、期限が切れるまでキックの対象にはならない。
    
使い方：
    BOTの権限はすべてオン
    configにて動作させたいBOTのId、一般スレッド、プレミアムスレッド、コンソールスレッドを設定する。
        一般スレッド：メッセージを読む、メッセージ履歴を読む、リアクションの追加の権限を追加
        プレミアムスレッド：そのまま
        コンソールスレッド：メッセージを読むの権限を削除
    
    管理者の人は
        ギフトコードが届いたら
            １：コンソールスレッドにて/pay1 user_name　を実行
                仮有料会員に追加することができる
                    有効期限は９時間
                    その間にギフトコードが有効かどうかを確認
                    もし有効でなければ
                        /undo pay1 user_name を実行することで取り消しが可能
            ２：ギフトコードが確認できればコンソールスレッドにて/pay2 user_name を実行
                相手にDMがそうしんされ、有料会員に追加することができる
                    一日あたり３３円の設定
        
        入れる人数を変えたいとき
            コンソールスレッドにて/sum 20　を実行
            最大値を２０に変更することができる
        
        課金ユーザを確認したいとき
            コンソールスレッドにて/listを実行
            課金ユーザと仮課金ユーザがリストされる

        コマンドがわからないとき
            コンソールスレッドにて/help を実行
            コマンドリストが出てくる

    一般ユーザーの人は
        ギフトコードを送信したあと
            プレミアムスレッドにて/pay user_name を実行
                仮有料会員になる
                    その間に管理人は確認せえよって話
            
            プレミアムスレッドにて/comform user_name を実行すると今の状況がわかる

Author: Masato Ishio
Date: 2020-10-02



"""
import discord
import datetime
import pickle
import random
import sys

#サーバに入れる最大人数（仮）
MAX_sum = 30

args = sys.argv
if args[1] == '-t':
    import configT
    #APIのkey
    TOKEN = configT.TOKEN
    ippanid = configT.ippanid
    consoleid = configT.consoleid
    premiamid = configT.premiamid
    # 絶対キック除外
    x = configT.x

else:
    import config
    #APIのkey
    TOKEN = config.TOKEN
    ippanid = config.ippanid
    consoleid = config.consoleid
    premiamid = config.premiamid
    # 絶対キック除外
    x = config.x

#最大人数を読み込み
try:
    with open("MAX_sum.pkl","rb") as f:
        MAX_sum = pickle.load(f)
except:
    print("NO File: MAX_sum.pkl")


# 課金者辞書
# paydic{"key":value,"ユーザー名",有効期限の時間}
paydic = {}
# 課金しているのかどうか確認する用の一時ユーザ辞書
prepaydic = {}

#プログラムが落ちたりしたときのために外部に保存
try:
    with open("paydic.pkl","rb") as f:
        paydic = pickle.load(f)
except:
    print("NO File: paydic.pkl")
try:
    with open("prepaydic.pkl","rb") as f:
        prepaydic = pickle.load(f)
except:
    print("NO File: prepaydic.pkl")

# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    msg = "やあ！TEST Botです．よろしくね！"
    channel = client.get_channel(ippanid)
    print("send hello")
    await channel.send(msg)


# 入ってきたとき
@client.event
async def on_member_join(member):
    channel = client.get_channel(ippanid)
    await channel.send(
        "ようこそ。："
        + str(member.mention)
        + "\nこのサーバでは人数を抑制するため人数を制限してます。\n制限を超えて入ってきた人がいると、はじめに入っていた人はキックされてしまいます。\nキックされた人はもう一度招待用のURLから入ってください。"
    )
    #キック用の関数を呼び出す
    await channel.send("/lol")


# 出るとき
@client.event
async def on_member_remove(member):
    channel = client.get_channel(consoleid)
    await channel.send(str(member.mention) + "が退出しました。")


@client.event
async def on_message(message):
    # Messageにはユーザから送られてきたメッセージに関する様々な情報が格納されています
    # /lol 自動キック関数
    global MAX_sum
    if (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/lol")
        and message.channel.id == ippanid
    ):

        #所属しているメンバー名とメンバーidを取得
        #実質削除されるかも用リスト
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        
        #消す条件に入っている人リスト
        dellist = []

        print(name)
        # name から絶対キック除外の人を削除
        for i in x:
            t1 = name.index(i)
            del name[t1]
            del nameid[t1]

        #課金ユーザの時間チェック
        # 辞書の時間と現在の時間を比較して小さかったら削除リストに追加
        # ループ中に増減させるのが良くない
        for i in paydic.keys():
            #有効期限までの時間をひかくしている
            if paydic[i] < datetime.datetime.utcnow() + datetime.timedelta(hours=9):
                dellist.append(i)
        
        # 有効期限が切れた課金ユーザにメッセージ送信
        for i in dellist:
            del paydic[i]
            t = name.index(i)
            user = client.get_user(nameid[t])
            #そのユーザにメッセージを送信
            await user.send("有料期間が終了しました")
            #一般にメッセージを送信
            await message.channel.send("@" + i + "の有料期間が終了しました。")

        # 課金者してくれているひとは削除されるかもしれないリストから削除
        for i in paydic.keys():
            try:
                t2 = name.index(i)
                del nameid[t2]
                del name[t2]
            except:
                pass

        #設定した制限より大きい限りユーザを削除する
        while len(name) > MAX_sum:
            #ランダムチョイス
            ran = random.randrange(MAX_sum)
            try:
                #キックされるユーザを選ぶ
                user = client.get_user(nameid[ran])
                await user.send("人数制限により自動的にキックされました。URLよりもう一度入ってください。")
            except:
                print("Error!!")
            user = discord.utils.get(message.guild.members, name=name[ran])
            #キックの実行
            await user.kick()
            
            #表示の形式を設定
            embed = discord.Embed(title="キックは正常に実行されました", color=0xFF0000)
            embed.set_thumbnail(url=user.avatar_url)
            embed.add_field(name="対象", value=user, inline=False)
            embed.add_field(name="実行", value=message.author, inline=False)
            
            #一般に送信
            await message.channel.send(embed=embed)
            
            #所属リストから削除
            del name[ran]
            del nameid[ran]
        
        #更新された課金ユーザを保存
        with open("paydic.pkl","wb") as f:
            pickle.dump(paydic,f)
        


    # list課金者を表示...
    # message.author.guild_permissions.administrator: administrator か判別
    #コンソールチャンネルで動作
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content == "/list"
        and message.channel.id == consoleid
    ):
        print("メッセージが送られました")
        print("送信者", message.author.display_name)
        print("内容", message.content)
        
        #課金してるか確認しなければならないユーザ
        prepay = ""
        #課金しているユーザ
        pay = ""
        
        for k, v in prepaydic.items():
            prepay = prepay + k + " : " + str(v) + "\n" 
        for k, v in paydic.items():
            pay = pay + k + " : " + str(v) + "\n"
        
        await message.channel.send("MAX_sum = " + str(MAX_sum))
        await message.channel.send("Prepaydic :\n" + prepay )
        # メッセージが送られたチャンネルにメッセージを送り返す
        await message.channel.send("paydic :\n" + pay)
        await message.channel.send("All elements were showed!!!")




    # 自分がconformプレミアムか確認
    # message.author.guild_permissions.administrator: administrator か判別
    #プレミアムチャンネル
    elif (
        message.author != client
        and message.content.startswith("/conform")
        and (message.channel.id == premiamid or message.channel.id == consoleid)
    ):
        name = message.author.display_name
        if name in paydic:
            await message.channel.send(name + "はプレミアムユーザです。")
        elif name in prepaydic:
            await message.channel.send(name + "のギフトカードを確認中です。少々お待ちください。")
        else:
            await message.channel.send(name + "はプレミアムユーザではありません。")

    # checkという内容の文が送られたら...
    # message.author.guild_permissions.administrator: administrator か判別
    #コードを送金したけど確認されてんのか心配になった人が送る
    #pay 自分のユーザ名
    elif (
        message.author != client
        and message.content.startswith("/pay")
        and message.channel.id == premiamid
    ):
        nameconfig = message.author.display_name
        args = message.content.split()
        #print("チェックします")
        #print("内容: " + args[1])
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        try:
            # 名前が存在するかどうか
            t = name.index(args[1])
        except:
            print("Error!!!")
            await message.channel.send("Error was happend!!!")
        else:
            print(nameid[t])
            if args[1] == nameconfig:
                #課金者辞書にある時
                if args[1] in paydic:
                    await message.channel.send("You are already PremiumUeser. \nPlease check using this commond: /conform")
                elif args[1] in prepaydic:
                #課金確認辞書にある時
                    await message.channel.send("ギフトコードが使えるか確認中です。少々お待ちください。")
                else:
                    # prepaydic に入れる
                    # 一日だけ有料期間
                    #payは確認辞書に入れてあげる
                    prepaydic[args[1]] = datetime.datetime.utcnow() + datetime.timedelta(days=1)
                    print(prepaydic)
                    
                    #更新されたので保存
                    with open("prepaydic.pkl", "wb") as f:
                        pickle.dump(prepaydic,f)
                    
                    # メッセージが送られたチャンネルにメッセージを送り返す
                    await message.channel.send(args[1] + "様、DMを送信しましたのでご確認ください。")
                    #ユーザに送り返す
                    user = client.get_user(nameid[t])
                    await user.send("ギフトコードが使えるかどうかチェックしております。最長1日ほどお時間を頂いております。 少々お待ちください。")
            else:
                #名前違うよアラート
                await message.channel.send("You are " + nameconfig +". You are NOT "+ args[1] + " !!!.")

    # checkという内容の文が送られたら...
    # message.author.guild_permissions.administrator: administrator か判別
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/pay1")
        and message.channel.id == consoleid
    ):
        nameconfig = message.author.display_name
        args = message.content.split()
        print("チェックします")
        #ユーザー名かもしれないしIDかもしれない
        print("内容: " + args[1])
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        try:
            # 名前が存在するかどうか
            t = name.index(args[1])
        except:
            print("Error!!!")
            await message.channel.send("Error was happend!!!")
        else:
            print(nameid[t])
            # prepaydic に入れる
            # 一日だけ有料期間
            prepaydic[args[1]] = datetime.datetime.utcnow() + datetime.timedelta(days=1)
            print(prepaydic)
            
            with open("prepaydic.pkl", "wb") as f:
                pickle.dump(prepaydic,f)
            
            # メッセージが送られたチャンネルにメッセージを送り返す
            await message.channel.send(args[1] + " was added prepaydic")
            #user = client.get_user(nameid[t])
            #await user.send("ギフトコードが使えるかどうかチェックしております。最長1日ほどお時間を頂いております。 少々お待ちください。")

    #課金者確認辞書から名前を削除する
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/undo pay1")
        and message.channel.id == consoleid
    ):
        args = message.content.split()
        print("チェックします")
        print("内容: " + args[2])
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        try:
            # 名前が存在するかどうか
            t = name.index(args[2])
            # prepaydicに名前があるか
            if args[2] not in prepaydic:
                raise Exception
        except:
            print("Error!!!")
            print(prepaydic)
            await message.channel.send("Error was happend!!!")
        else:
            # prepaydic に入れる
            # 一日だけ有料期間
            del prepaydic[args[2]]
            with open("prepaydic.pkl","wb") as f:
                pickle.dump(prepaydic, f)
            
            print(prepaydic)
            # メッセージが送られたチャンネルにメッセージを送り返す
            await message.channel.send("Success /undo pay1 " + args[2] + " !!!")
            #user = client.get_user(nameid[t])
            #await user.send("ギフトコードが確認できませんでした")

    #課金者辞書に入れる
    #pay2 名前　金額
    #pay2 haruki 1000
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/pay2")
        and message.channel.id == consoleid
    ):
        args = message.content.split()
        print("チェックします")
        print("名前: " + args[1])
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        try:
            # 名前が存在するかどうか
            # prepaydicに入ってなかったらエラー
            if args[1] in prepaydic:
                pass
            else:
                raise Exception
            # 円が存在するかどうか
            en = int(args[2])
        except:
            print("Error!!!")
            await message.channel.send("Error was happend!!!")
        else:
            # 計算
            print("円: " + str(en))
            
            # 一日33円ぐらい
            day = en // 33
            print("日: " + str(day))
            t = name.index(args[1])
            user = client.get_user(nameid[t])
            dt_now = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
            # 終わりの日を計算
            dt_end = dt_now + datetime.timedelta(days=day)
            print(dt_now)
            print(dt_end)
            await message.channel.send("Addid!!")
            
            # 名前を値、時間をキーにして追加
            del prepaydic[args[1]]
            paydic[args[1]] = dt_end
            with open("prepaydic.pkl", "wb") as f:
                pickle.dump(prepaydic, f)
            with open("paydic.pkl", "wb")as f:
                pickle.dump(paydic,f)

            print(prepaydic)
            print(paydic)
            
            #課金してくれた人に直接メッセージ
            await user.send("ギフトコードが確認されました。有効期限は" + str(dt_end) + "までです")

    #課金者辞書から削除
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/undo pay2")
        and message.channel.id == consoleid
    ):
        args = message.content.split()
        print("チェックします")
        print("内容: " + args[2])
        name = [member.name for member in message.guild.members]
        nameid = [member.id for member in message.guild.members]
        try:
            # 名前が存在するかどうか
            t = name.index(args[2])
            # prepaydicに名前があるか
            if args[2] not in paydic:
                raise Exception
        except:
            print("Error!!!")
            print(paydic)
            await message.channel.send("Error was happend!!!")
        else:
            # paydic を削除
            del paydic[args[2]]
            with open("paydic.pkl","wb")as f:
                    pickle.dump(paydic, f)

            print(paydic)
            # メッセージが送られたチャンネルにメッセージを送り返す
            await message.channel.send("Success /undo pay2 " + args[2] + " !!!")
            #user = client.get_user(nameid[t])
            #await user.send("")

    #サーバーに入れるマックス人数を指定
    #/sum 1000
    #最大1000人似設定
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/sum")
        and message.channel.id == consoleid
    ):
        
        args = message.content.split()
        try:
            MAX_sum = int(args[1])
        except:
            await message.channel.send("Error was happend!!!")
        else:
            with open("MAX_sum.pkl", "wb") as f:
                pickle.dump(MAX_sum,f)
            await message.channel.send("Success!!! MAX_sum = " + str(MAX_sum))
            channel = client.get_channel(ippanid)
            #/lolで呼び出される関数
            #自動キック関数
            await channel.send('/lol')

    #使い方説明
    elif (
        message.author != client
        and message.author.guild_permissions.administrator
        and message.content.startswith("/help")
        and message.channel.id == consoleid
    ):
        
        st = ("/lol : 一般 - キック\n/list : console - paydicとprepaydicを確認\n/conform : プレミアム, console - 打ったユーザがプレミアムかどうか確認できる。\n/pay hoge : プレミアム - hogeをprepaydicに追加、DM送信\n/pay1 : console - prepaydicに追加\n/undo pay1 hoge : console - prepaydicからhogeを削除\n/pay2 hoge : console - hogeをpaydicに追加、DM送信\n/undo pay2 hog : console - hogeをpaydicから削除\n/sum 4: console - 4に最大人数を変更")
        await message.channel.send(st)

    # Botからのメッセージには応答しない
    elif message.author.bot:
        return


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)

