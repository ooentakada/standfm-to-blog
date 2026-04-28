#!/usr/bin/env python3
"""
Stand.fm音声を文字起こしするスクリプト
使い方: python3 transcribe.py "<Stand.fm URL>"
"""
import os, sys, re, subprocess, tempfile, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
CONTENT_DIR = os.environ.get("CONTENT_DIR", "content")

def get_audio_url_from_rss(episode_url: str) -> str | None:
    """RSSフィードからエピソードの音声URLを取得"""
    # episode_urlからチャンネルIDを推測してRSSを試みる
    # Stand.fmのRSSは https://stand.fm/rss/{channel_id}
    m = re.search(r'stand\.fm/episodes/([a-zA-Z0-9]+)', episode_url)
    if not m:
        return None
    episode_id = m.group(1)

    # RSSを検索（チャンネルIDが必要なので直接エピソードページから取得を試みる）
    return get_audio_url_from_page(episode_url)

def get_audio_url_from_page(episode_url: str) -> str | None:
    """エピソードページのHTMLから音声URLを直接取得"""
    try:
        req = urllib.request.Request(episode_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")
        # 音声URLのパターンを探す
        patterns = [
            r'"(https://cdncf\.stand\.fm/audios/[^"]+\.m4a)"',
            r'"(https://[^"]+\.stand\.fm/[^"]+\.m4a)"',
            r'(https://cdncf\.stand\.fm/audios/[^\s"\']+)',
        ]
        for pat in patterns:
            m = re.search(pat, html)
            if m:
                return m.group(1)
    except Exception as e:
        print(f"ページ取得エラー: {e}")
    return None

def download_audio(url: str, dest: str) -> bool:
    """音声ファイルをダウンロード"""
    print(f"音声をダウンロード中...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        Path(dest).write_bytes(r.read())
    size_mb = Path(dest).stat().st_size / 1024 / 1024
    print(f"ダウンロード完了: {size_mb:.1f}MB")
    return True

def convert_to_wav(src: str, dest: str) -> bool:
    """ffmpegでWAVに変換"""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", dest],
        capture_output=True, text=True
    )
    return result.returncode == 0

def transcribe_with_whisper(wav_path: str) -> str:
    """Whisper APIで文字起こし"""
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("Whisper APIで文字起こし中...")
    with open(wav_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ja"
        )
    return result.text

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 transcribe.py '<Stand.fm URL>'")
        sys.exit(1)

    episode_url = sys.argv[1]
    if "stand.fm/episodes/" not in episode_url:
        print("エラー: Stand.fmのエピソードURLを指定してください")
        sys.exit(1)

    print(f"エピソード: {episode_url}")

    # 音声URL取得
    audio_url = get_audio_url_from_page(episode_url)
    if not audio_url:
        print("エラー: 音声URLが見つかりませんでした")
        sys.exit(1)
    print(f"音声URL: {audio_url}")

    # 保存先フォルダ作成
    date_str = datetime.now().strftime("%Y%m%d")
    transcript_dir = Path(CONTENT_DIR) / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        # ダウンロード
        audio_path = f"{tmpdir}/audio.m4a"
        download_audio(audio_url, audio_path)

        # WAV変換
        wav_path = f"{tmpdir}/audio.wav"
        if not convert_to_wav(audio_path, wav_path):
            print("警告: ffmpegでの変換に失敗。m4aのまま文字起こしを試みます")
            wav_path = audio_path

        # 文字起こし
        text = transcribe_with_whisper(wav_path)

    # 保存
    out_path = transcript_dir / f"{date_str}-transcript.txt"
    out_path.write_text(text, encoding="utf-8")
    print(f"\n文字起こし完了: {out_path}")
    print(f"文字数: {len(text)}文字")
    return str(out_path)

if __name__ == "__main__":
    main()
