#!/usr/bin/env python3
"""
note記事投稿スクリプト（汎用版）
使い方: python3 note_post.py <記事.md> [アイキャッチ画像.png]

設定:
  NOTE_USER_URLNAME  : noteのURL名（例: ooenfes）
  NOTE_SESSION_FILE  : セッションファイルのパス
"""
import sys, os, re, tempfile
from pathlib import Path
from PIL import Image

NOTE_USER_URLNAME = os.environ.get("NOTE_USER_URLNAME", "")
NOTE_SESSION_FILE = os.environ.get(
    "NOTE_SESSION_FILE",
    str(Path(__file__).parent.parent / "note_session.json")
)

def parse_article(md_path: str) -> dict:
    text = Path(md_path).read_text(encoding="utf-8")
    title = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else text
        m = re.search(r'^title:\s*(.+)$', parts[1], re.MULTILINE)
        title = m.group(1).strip() if m else ""
    else:
        body = text.strip()
    lines = body.split("\n")
    # frontmatterにtitleがあっても本文のH1を除去
    if lines and lines[0].startswith("# "):
        if not title:
            title = lines[0][2:].strip()
        body = "\n".join(lines[1:]).strip()
    return {"title": title, "body": body}

def resize_eyecatch(src: str) -> str:
    """noteのアイキャッチは1280×670必須。リサイズして一時ファイルに保存"""
    img = Image.open(src)
    if img.size == (1280, 670):
        return src
    resized = img.resize((1280, 670), Image.LANCZOS)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    resized.save(tmp.name, "PNG")
    print(f"アイキャッチを1280×670にリサイズしました")
    return tmp.name

def ensure_session():
    session_path = Path(NOTE_SESSION_FILE)
    if not session_path.exists():
        raise RuntimeError(
            f"セッションファイルが見つかりません: {NOTE_SESSION_FILE}\n"
            "先に setup_note_session.py を実行してください"
        )
    import requests, json
    data = json.loads(session_path.read_text())
    cookies = data.get("cookies", {})
    resp = requests.get(
        "https://note.com/api/v3/users/user_features",
        cookies=cookies,
        headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    )
    if resp.status_code != 200:
        raise RuntimeError(
            "noteのセッションが切れています。\n"
            "setup_note_session.py を再実行してください"
        )

def make_abs_paths(body: str, base_dir: str) -> str:
    """記事内の相対パス画像を絶対パスに変換（S3アップロードエラー対策）"""
    def replace(m):
        alt, path = m.group(1), m.group(2)
        if not path.startswith("/") and not path.startswith("http"):
            path = str(Path(base_dir) / path)
        return f"![{alt}]({path})"
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace, body)

def post_to_note(title: str, body: str, eyecatch_path: str = None) -> str:
    from NoteClient2 import NoteClient2
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(body)
        tmp_path = tmp.name

    client = NoteClient2(
        email="dummy@example.com",
        password="dummy",
        user_urlname=NOTE_USER_URLNAME,
        session_file=NOTE_SESSION_FILE,
    )

    eyecatch_resized = resize_eyecatch(eyecatch_path) if eyecatch_path else None

    result = client.publish(
        title=title,
        md_file_path=tmp_path,
        eyecatch_path=eyecatch_resized,
        hashtags=[],
        price=0,
        is_publish=True
    )
    Path(tmp_path).unlink(missing_ok=True)

    if not result.get("ok"):
        raise RuntimeError(f"投稿エラー: {result.get('error', {})}")
    return result["data"]["public_url"]

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 note_post.py <記事.md> [アイキャッチ.png]")
        sys.exit(1)

    if not NOTE_USER_URLNAME:
        print("エラー: NOTE_USER_URLNAME が設定されていません")
        print(".claude/standfm-to-blog.env を確認してください")
        sys.exit(1)

    md_path = sys.argv[1]
    eyecatch = sys.argv[2] if len(sys.argv) >= 3 else None

    article = parse_article(md_path)
    print(f"タイトル: {article['title']}")
    print(f"文字数: {len(article['body'])}文字")

    # 画像パスを絶対パスに変換
    base_dir = str(Path(md_path).parent.parent)  # content/drafts → プロジェクトルート
    body_abs = make_abs_paths(article["body"], base_dir)

    ensure_session()
    print("noteに投稿中...")
    url = post_to_note(article["title"], body_abs, eyecatch_path=eyecatch)
    print(f"\n✓ 投稿完了！")
    print(f"URL: {url}")

if __name__ == "__main__":
    main()
