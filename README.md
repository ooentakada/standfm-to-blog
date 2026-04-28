# Stand.fm → ブログ自動投稿スキル

**Stand.fmのURLを貼るだけで、記事を自動生成してnote・WordPressに投稿するClaude Codeスキルです。**

---

## できること

```
URLをチャットに貼る
      ↓
🎙️ 音声を自動で文字起こし（Whisper）
      ↓
✍️ note版・WordPress版の記事を2本生成
      ↓
🖼️ 4コマ漫画＋バナー画像を自動生成
      ↓
📸 一緒に貼った写真を記事に自動配置
      ↓
🚀 note・WordPressに同時投稿
```

URLを貼ってから投稿完了まで約10〜15分。

---

## インストール方法

### Step 1: このフォルダをダウンロードして解凍

ZIPを解凍すると `standfm-to-blog/` フォルダができます。

### Step 2: インストールスクリプトを実行

Claude Codeのプロジェクトルート（`.claude` フォルダがある場所）で実行:

```bash
bash ~/Downloads/standfm-to-blog/install.sh
```

これだけで:
- スキルファイルが `.claude/skills/standfm-to-blog/` にコピーされます
- 設定ファイルのテンプレートが `.claude/standfm-to-blog.env` に作成されます
- Pythonライブラリが自動インストールされます

### Step 3: 設定ファイルを記入

`.claude/standfm-to-blog.env` を開いて記入します:

```env
# OpenAI APIキー（必須）
# https://platform.openai.com/api-keys で発行
OPENAI_API_KEY=sk-xxxx...

# 投稿先: none / note / wordpress / both
PUBLISH_TARGET=both

# --- noteの設定（noteを使わない場合は空白でOK） ---
NOTE_USER_URLNAME=あなたのnote URL名（例: note.com/yamada → yamada）
NOTE_SESSION_FILE=.claude/skills/standfm-to-blog/note_session.json

# --- WordPressの設定（WordPressを使わない場合は空白でOK） ---
WP_SITE_URL=https://あなたのサイト.com
WP_USERNAME=管理者ユーザー名
WP_APP_PASSWORD=アプリケーションパスワード
```

#### WordPressのアプリケーションパスワードの取得方法
1. WordPress管理画面 → 「ユーザー」→「プロフィール」
2. 「アプリケーションパスワード」セクションでアプリ名を入力
3. 表示されたパスワード（スペース区切りの英数字）をそのままコピー

### Step 4: noteのセッション設定（noteを使う場合のみ）

```bash
python3 .claude/skills/standfm-to-blog/scripts/setup_note_session.py
```

Chromeが開くのでnote.comにログインして、Enterを押すと完了。

### Step 5: Claude Codeを再起動

設定を読み込ませるために一度再起動してください。

---

## 使い方

### 基本: URLを貼るだけ

```
https://stand.fm/episodes/xxxxxxxxxxxxxxxx
```

これだけで全自動で動きます。

### 写真も一緒に投稿したい場合

URLと一緒に写真をチャットにドラッグ＆ドロップ:

```
https://stand.fm/episodes/xxxxxxxxxxxxxxxx

[写真をドラッグ＆ドロップ]
```

写真の内容を自動判定して、記事の適切な場所に配置します。

### 文体を自分のものにしたい

`knowledge/style/writing-guide.md` に自分の文体ルールを書いてください。
スキルがそれを読んで記事を生成します。

---

## 生成されるファイル

| ファイル | 内容 |
|---------|------|
| `content/transcripts/（日付）-transcript.txt` | 文字起こしテキスト |
| `content/drafts/（日付）-note-（タイトル）.md` | note向け記事 |
| `content/drafts/（日付）-wordpress-（タイトル）.md` | WordPress向け記事 |
| `content/images/（日付）-manga.png` | 4コマ漫画 |
| `content/images/（日付）-banner.png` | バナー画像 |

---

## よくあるトラブル

| エラー | 原因 | 対処 |
|--------|------|------|
| `ffmpegがありません` | ffmpeg未インストール | `brew install ffmpeg` を実行 |
| `S3UploadFailed (204)` | NoteClient2のバグ | 下記「NoteClient2のバグ修正」を参照 |
| `noteアイキャッチエラー` | 画像サイズ問題 | スキルが自動でリサイズします |
| `WordPress 401エラー` | 認証問題 | XML-RPC方式で自動対処済み |
| `セッションが切れています` | noteのCookie期限切れ | `setup_note_session.py` を再実行 |

### NoteClient2のバグ修正（S3エラーが出た場合）

```bash
python3 -c "
import pathlib
f = list(pathlib.Path().rglob('NoteClient2/http.py'))[0]
txt = f.read_text()
fixed = txt.replace('ok = resp.status_code in (200, 201)', 'ok = resp.status_code in (200, 201, 204)')
f.write_text(fixed)
print('修正完了:', f)
"
```

---

## 必要なもの

| 項目 | 用途 | 入手先 |
|------|------|--------|
| OpenAI APIキー | 文字起こし＋画像生成 | platform.openai.com |
| Python 3.9以上 | スクリプト実行 | python.org |
| ffmpeg | 音声変換 | `brew install ffmpeg` |
| noteアカウント | 投稿先（任意） | note.com |
| WordPressサイト | 投稿先（任意） | — |

noteもWordPressも持っていない場合は `PUBLISH_TARGET=none` で文字起こし＋記事生成だけ使えます。

---

作成: Claude Code実践会（よーへいさん & AI秘書ハル）
