#!/usr/bin/env python3
"""
noteセッション設定スクリプト
ChromeでNote.comにログインした状態で実行するとCookieを保存します

使い方: python3 setup_note_session.py

設定:
  NOTE_SESSION_FILE : セッションファイルの保存先
"""
import os, json, sys
from pathlib import Path

NOTE_SESSION_FILE = os.environ.get(
    "NOTE_SESSION_FILE",
    str(Path(__file__).parent.parent / "note_session.json")
)

def setup_with_selenium():
    """Selenium + Chromeを使ってCookieを取得"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError:
        print("エラー: Seleniumがインストールされていません")
        print("インストール: pip3 install selenium")
        sys.exit(1)

    print("ChromeでNote.comを開きます...")
    print("すでにChromeにログイン済みのプロファイルを使います。")
    print()

    options = Options()
    # ユーザーのChromeプロファイルを使う（すでにログイン済みの状態）
    import platform
    if platform.system() == "Darwin":
        profile_dir = Path.home() / "Library/Application Support/Google/Chrome"
    elif platform.system() == "Windows":
        profile_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data"
    else:
        profile_dir = Path.home() / ".config/google-chrome"

    if profile_dir.exists():
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")

    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    print("note.comにアクセス中...")
    driver.get("https://note.com/login")

    print()
    print("=" * 50)
    print("【操作が必要です】")
    print("Chromeが開きました。")
    print("note.comにログインしてください。")
    print("ログイン完了後、Enterキーを押してください。")
    print("=" * 50)
    input("Enterキーを押してください > ")

    # Cookieを取得
    cookies = driver.get_cookies()
    driver.quit()

    if not cookies:
        print("エラー: Cookieが取得できませんでした")
        sys.exit(1)

    # note関連のCookieだけ抽出
    note_cookies = {c["name"]: c["value"] for c in cookies if "note" in c.get("domain", "")}

    if not note_cookies:
        print("エラー: note.comのCookieが見つかりません")
        print("note.comにログインした状態で再度実行してください")
        sys.exit(1)

    # 保存
    session_path = Path(NOTE_SESSION_FILE)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_data = {"cookies": note_cookies, "all_cookies": cookies}
    session_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2))

    print(f"\nセッション保存完了: {NOTE_SESSION_FILE}")
    print(f"取得したCookie数: {len(note_cookies)}")
    return True

def verify_session():
    """保存したセッションが有効か確認"""
    session_path = Path(NOTE_SESSION_FILE)
    if not session_path.exists():
        print(f"セッションファイルが見つかりません: {NOTE_SESSION_FILE}")
        return False

    try:
        import requests
        data = json.loads(session_path.read_text())
        cookies = data.get("cookies", {})
        resp = requests.get(
            "https://note.com/api/v3/users/user_features",
            cookies=cookies,
            headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"},
            timeout=10
        )
        if resp.status_code == 200:
            print("セッション有効です！")
            return True
        else:
            print(f"セッションが無効です（HTTP {resp.status_code}）")
            return False
    except Exception as e:
        print(f"確認中にエラー: {e}")
        return False

def main():
    print("=== noteセッション設定ツール ===")
    print()

    # 既存セッションを確認
    session_path = Path(NOTE_SESSION_FILE)
    if session_path.exists():
        print("既存のセッションファイルが見つかりました。確認中...")
        if verify_session():
            print("現在のセッションは有効です。更新は不要です。")
            ans = input("それでも更新しますか？ [y/N] > ").strip().lower()
            if ans != "y":
                print("キャンセルしました。")
                return
        else:
            print("セッションが無効なので再設定します。")

    print()
    setup_with_selenium()
    print()
    print("設定完了！note投稿スクリプトが使えます。")
    print(f"  python3 scripts/note_post.py <記事.md> [アイキャッチ.png]")

if __name__ == "__main__":
    main()
