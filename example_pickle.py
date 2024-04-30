import dotenv
import os
import pickle
import tweepy
from pathlib import Path
from tweepy_authlib import CookieSessionUserHandler

try:
    terminal_size = os.get_terminal_size().columns
except OSError:
    terminal_size = 80

# ユーザー名とパスワードを環境変数から取得
dotenv.load_dotenv()
screen_name = os.environ.get('TWITTER_SCREEN_NAME', 'your_screen_name')
password = os.environ.get('TWITTER_PASSWORD', 'your_password')

# 保存した Cookie を使って認証
## 毎回ログインすると不審なログインとして扱われる可能性が高くなるため、
## できるだけ以前認証した際に保存した Cookie を使って認証することを推奨
if Path('cookie.pickle').exists():

    # 保存した Cookie を読み込む
    with open('cookie.pickle', 'rb') as f:
        cookies = pickle.load(f)

    # 読み込んだ RequestCookieJar オブジェクトを CookieSessionUserHandler に渡す
    auth_handler = CookieSessionUserHandler(cookies=cookies)

# スクリーンネームとパスワードを指定して認証
else:

    # スクリーンネームとパスワードを渡す
    ## スクリーンネームとパスワードを指定する場合は初期化時に認証のための API リクエストが多数行われるため、完了まで数秒かかる
    try:
        auth_handler = CookieSessionUserHandler(screen_name=screen_name, password=password)
    except tweepy.HTTPException as ex:
        # パスワードが間違っているなどの理由で認証に失敗した場合
        if len(ex.api_codes) > 0 and len(ex.api_messages) > 0:
            error_message = f'Code: {ex.api_codes[0]}, Message: {ex.api_messages[0]}'
        else:
            error_message = 'Unknown Error'
        raise Exception(f'Failed to authenticate with password ({error_message})')
    except tweepy.TweepyException as ex:
        # 認証フローの途中で予期せぬエラーが発生し、ログインに失敗した
        error_message = f'Message: {ex}'
        raise Exception(f'Unexpected error occurred while authenticate with password ({error_message})')

    # 現在のログインセッションの Cookie を取得
    cookies = auth_handler.get_cookies()

    # Cookie を pickle 化して保存
    with open('cookie.pickle', 'wb') as f:
        pickle.dump(cookies, f)

# Tweepy で Twitter API v1.1 にアクセス
api = tweepy.API(auth_handler)
print('-' * terminal_size)
print(api.verify_credentials())
print('-' * terminal_size)

# 継続してログインしない場合は明示的にログアウト
## 単に Cookie を消去するだけだと Twitter にセッションが残り続けてしまう
## ログアウト後は、取得した Cookie では再認証できなくなる
#auth_handler.logout()
#os.unlink('cookie.pickle')
