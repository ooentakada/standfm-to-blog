---
name: standfm-to-blog
description: Stand.fmの音声配信URLを貼るだけで、文字起こし→記事生成→画像生成→note/WordPress自動投稿まで全自動で完結するスキル。「Stand.fmを記事にして」「音声を投稿して」「standfm展開して」「このURLをブログにして」と言われたら必ずこのスキルを使う。メッセージに「stand.fm/episodes/」を含むURLがあれば即起動。写真を一緒に共有された場合は記事・バナーに自動組み込み。
---

# Stand.fm → ブログ自動投稿スキル

Stand.fmのエピソードURLを受け取り、文字起こし→記事生成→画像生成→投稿まで全自動で実行する。

---

## 前提チェック（スキル起動時に必ず実行）

```bash
# 設定ファイルの確認
ls .claude/standfm-to-blog.env 2>/dev/null || echo "設定ファイルがありません"
```

設定ファイルがない場合: `setup.env.example` を `.claude/standfm-to-blog.env` にコピーして設定を促す。

設定ファイルがある場合:
```bash
source .claude/standfm-to-blog.env
export OPENAI_API_KEY CONTENT_DIR PUBLISH_TARGET
export NOTE_USER_URLNAME NOTE_SESSION_FILE
export WP_SITE_URL WP_USERNAME WP_APP_PASSWORD
```

---

## Step 1: 文字起こし

```bash
source .claude/standfm-to-blog.env
python3 .claude/skills/standfm-to-blog/scripts/transcribe.py "<Stand.fm URL>"
```

出力先: `content/transcripts/（日付）-transcript.txt`

完了したらファイルを読んで内容を把握する。

---

## Step 2: 写真の取り込み（ある場合のみ）

ユーザーが写真を貼った場合: 写真を `content/images/` に保存して記事に組み込む。

写真の命名: 内容がわかる名前にする（例: `event-crowd.jpg`, `hands-on-session.jpg`）

写真を複数枚もらった場合は内容を見て適切なセクションに振り分ける:
- 全体写真・会場写真 → 記事冒頭
- 作業中・デモ写真 → 内容説明セクション
- 集合写真 → 記事末尾

---

## Step 3: 記事生成（2バージョン）

文字起こし全文を読んで、2種類の記事を生成する。

**note向け記事** (`content/drafts/（日付）-note-（タイトル）.md`):
- フォーマット: 体験・物語・共感重視
- 冒頭: 「なぜ今この話をするか・読む価値」を前面に出す
- 構成: リード → H2見出し3〜5セクション → まとめ → エピソードへのリンク
- 写真: 物語の流れに合わせて配置
- トーン: 内省的・正直・読者への問いかけあり

**WordPress向け記事** (`content/drafts/（日付）-wordpress-（タイトル）.md`):
- フォーマット: How-to・実践・SEO重視
- 冒頭: note版とは別の書き出し（検索意図を意識）
- 構成: note版と同じテーマだがH2/H3必須・箇条書き多用・Before/After例・表を活用
- 写真: 解説の補足として配置
- トーン: 実用的・手順重視

**両記事の共通ルール:**
- frontmatterに `title:` を記載する
- 記事冒頭のH1（`# タイトル`）は書いてもよい（投稿スクリプトが自動除去）
- 一人称はユーザーの文体に合わせる
- 冒頭3行でスクロールを止める
- 数字・具体エピソードを必ず入れる

記事の文体は `knowledge/style/writing-guide.md` があれば読んで参照する。

---

## Step 4: 画像生成（2種類）

OpenAI gpt-image-2で生成する。

**4コマ漫画** (`content/images/（日付）-manga.png`):
```python
from openai import OpenAI
import base64, os
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
result = client.images.generate(
    model="gpt-image-2",
    prompt="（記事内容から4コマ漫画のプロンプトを生成）",
    size="1024x1536",
    quality="high"
)
img_data = base64.b64decode(result.data[0].b64_json)
open("content/images/（日付）-manga.png", "wb").write(img_data)
```

プロンプトの書き方:
- 記事のキーメッセージを4コマのストーリーに凝縮
- 日本語セリフ入り、白黒漫画スタイル
- 起承転結を明確に

**バナー画像** (`content/images/（日付）-banner.png`):
```python
result = client.images.generate(
    model="gpt-image-2",
    prompt="（記事タイトルとキービジュアルのバナープロンプト）",
    size="1536x1024",
    quality="high"
)
```

プロンプトの書き方:
- 記事のタイトルと主要メッセージを視覚化
- 横長バナー形式（16:9相当）
- プロフェッショナルなデザイン、テキスト要素は最小限に

---

## Step 5: 投稿

設定ファイルの `PUBLISH_TARGET` に従って投稿先を決定:
- `none` → 投稿しない（ファイルを表示して終了）
- `note` → noteだけに投稿
- `wordpress` → WordPressだけに投稿
- `both` → 両方に投稿

### note投稿

```bash
source .claude/standfm-to-blog.env
python3 .claude/skills/standfm-to-blog/scripts/note_post.py \
  "content/drafts/（日付）-note-（タイトル）.md" \
  "content/images/（日付）-banner.png"
```

- 4コマ漫画は `note_post.py` が記事冒頭に挿入する
- バナーはアイキャッチとして設定（1280×670に自動リサイズ）

**事前確認:**
```bash
python3 -c "import json, pathlib; d=json.loads(pathlib.Path('$NOTE_SESSION_FILE').read_text()); print('OK' if d.get('cookies') else 'NO')" 2>/dev/null || echo "セッションなし"
```
セッションがない場合: `python3 .claude/skills/standfm-to-blog/scripts/setup_note_session.py` を実行して案内する。

### WordPress投稿

```bash
source .claude/standfm-to-blog.env
python3 .claude/skills/standfm-to-blog/scripts/wp_post.py \
  "content/drafts/（日付）-wordpress-（タイトル）.md" \
  "content/images/（日付）-manga.png" \
  "content/images/（日付）-banner.png"
```

- 4コマ漫画が記事冒頭に挿入される
- バナーがアイキャッチ（フィーチャードイメージ）として設定される

---

## Step 6: 完了報告

投稿完了後にURLを報告する:
- note: `https://note.com/（ユーザー名）/n/（記事ID）`
- WordPress: `https://（サイトURL）/?p=（記事ID）`

---

## エラー対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `S3UploadFailed (204)` | NoteClient2のバグ | `scripts/fix_noteclient2.py` を実行 |
| `noteアイキャッチ縦横比エラー` | サイズ問題 | `note_post.py` が自動で1280×670にリサイズ |
| `WordPress 401エラー` | 認証ヘッダー問題 | XML-RPC方式を使用（自動） |
| `セッションが切れています` | noteのCookieが期限切れ | `setup_note_session.py` を再実行 |
| `音声URLが見つかりません` | Stand.fmのページ構造変更 | HTMLから手動で音声URLを探してtranscribe.pyのURLを直接指定 |
| `ffmpegがありません` | ffmpeg未インストール | `brew install ffmpeg`（Mac）または `winget install ffmpeg`（Windows） |

---

## ファイル構造

```
.claude/skills/standfm-to-blog/
├── SKILL.md               ← このファイル
├── README.md              ← セットアップ手順（配布先向け）
├── setup.env.example      ← 設定ファイルのテンプレート
└── scripts/
    ├── transcribe.py      ← 文字起こし
    ← note_post.py         ← note投稿
    ├── wp_post.py         ← WordPress投稿
    └── setup_note_session.py ← noteセッション設定

content/                   ← 生成物の保存先
├── transcripts/           ← 文字起こしテキスト
├── drafts/                ← 記事の下書き（note版・WordPress版）
└── images/                ← 生成画像・取り込み写真
```
