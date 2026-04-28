#!/bin/bash
# Stand.fm → ブログ自動投稿スキル インストーラー
# 使い方: bash install.sh をプロジェクトのルートで実行してください

set -e

SKILL_DIR=".claude/skills/standfm-to-blog"
ENV_FILE=".claude/standfm-to-blog.env"

# スクリプトのある場所（展開先）を基準にする
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "======================================"
echo " Stand.fm → ブログ スキル インストーラー"
echo "======================================"
echo ""

# .claude フォルダの確認
if [ ! -d ".claude" ]; then
  echo "エラー: .claude フォルダが見つかりません"
  echo "Claude Codeのプロジェクトルートで実行してください"
  echo ""
  echo "（例）cd ~/my-project && bash ~/Downloads/standfm-to-blog/install.sh"
  exit 1
fi

# スキルフォルダにコピー
echo "スキルファイルをインストール中..."
mkdir -p "$SKILL_DIR/scripts"
cp "$SCRIPT_DIR/SKILL.md"                    "$SKILL_DIR/"
cp "$SCRIPT_DIR/scripts/transcribe.py"        "$SKILL_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/note_post.py"         "$SKILL_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/wp_post.py"           "$SKILL_DIR/scripts/"
cp "$SCRIPT_DIR/scripts/setup_note_session.py" "$SKILL_DIR/scripts/"
echo "  → $SKILL_DIR/ にコピー完了"

# 設定ファイルの作成
if [ ! -f "$ENV_FILE" ]; then
  cp "$SCRIPT_DIR/setup.env.example" "$ENV_FILE"
  echo "  → $ENV_FILE を作成しました（設定を記入してください）"
else
  echo "  → $ENV_FILE はすでに存在します（上書きしません）"
fi

# Pythonライブラリのインストール
echo ""
echo "Pythonライブラリをインストール中..."
pip3 install openai requests pillow NoteClient2 --quiet && echo "  → インストール完了" || echo "  → 一部失敗しました。pip3 install openai requests pillow NoteClient2 を手動で実行してください"

# ffmpegの確認
echo ""
if command -v ffmpeg &> /dev/null; then
  echo "ffmpeg: インストール済み ✓"
else
  echo "ffmpeg: 未インストール"
  echo "  → 文字起こしに必要です。brew install ffmpeg でインストールしてください"
fi

echo ""
echo "======================================"
echo " インストール完了！"
echo "======================================"
echo ""
echo "次にやること:"
echo ""
echo "1. 設定ファイルを開いて記入する:"
echo "   open $ENV_FILE   （または好きなエディタで開く）"
echo ""
echo "2. noteを使う場合はセッション設定:"
echo "   python3 $SKILL_DIR/scripts/setup_note_session.py"
echo ""
echo "3. Claude Codeを再起動してから使えます"
echo ""
echo "使い方: Stand.fmのURLをチャットに貼るだけ！"
echo "  例: https://stand.fm/episodes/xxxxxxxx"
