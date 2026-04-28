#!/usr/bin/env python3
"""
WordPress記事投稿スクリプト（汎用版・XML-RPC方式）
使い方: python3 wp_post.py <記事.md> [4コマ漫画.png] [バナー.png]

設定:
  WP_SITE_URL     : WordPressサイトURL
  WP_USERNAME     : 管理者ユーザー名
  WP_APP_PASSWORD : アプリケーションパスワード
"""
import os, sys, re, base64, mimetypes, urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

WP_SITE_URL = os.environ.get("WP_SITE_URL", "").rstrip("/")
WP_USERNAME = os.environ.get("WP_USERNAME", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

def escape_xml(s: str) -> str:
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def xmlrpc(method: str, params_xml: str) -> ET.Element:
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<methodCall>
  <methodName>{method}</methodName>
  <params>{params_xml}</params>
</methodCall>"""
    req = urllib.request.Request(
        f"{WP_SITE_URL}/xmlrpc.php",
        data=body.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())

def upload_image(path: str, name: str) -> tuple[str, str]:
    """画像をWordPressメディアライブラリにアップロード。(URL, ID)を返す"""
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    params = f"""
<param><value><int>1</int></value></param>
<param><value><string>{WP_USERNAME}</string></value></param>
<param><value><string>{WP_APP_PASSWORD}</string></value></param>
<param><value><struct>
  <member><name>name</name><value><string>{escape_xml(name)}</string></value></member>
  <member><name>type</name><value><string>{mime}</string></value></member>
  <member><name>bits</name><value><base64>{b64}</base64></value></member>
  <member><name>overwrite</name><value><boolean>0</boolean></value></member>
</struct></value></param>"""
    root = xmlrpc("wp.uploadFile", params)
    url = root.findtext(".//member[name='url']/value/string")
    id_ = root.findtext(".//member[name='id']/value/string") or \
          root.findtext(".//member[name='id']/value/int") or ""
    return url, id_

def md_to_html(md: str, image_url_map: dict) -> str:
    """MarkdownをHTML変換。画像パスはWordPress URLに置換"""
    lines = md.split("\n")
    html = []
    in_ul = in_table = in_code = False

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True; html.append("<pre><code>")
            else:
                in_code = False; html.append("</code></pre>")
            continue
        if in_code:
            html.append(line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
            continue

        def bold(s): return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        def link(s): return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)

        if line.startswith("# "):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            if in_ul: html.append("</ul>"); in_ul = False
            html.append(f"<h3>{line[4:]}</h3>")
        elif line.strip() == "---":
            if in_ul: html.append("</ul>"); in_ul = False
            html.append("<hr>")
        elif re.match(r'!\[', line.strip()):
            if in_ul: html.append("</ul>"); in_ul = False
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
            if m:
                alt, path = m.group(1), m.group(2)
                fname = Path(path).name
                wp_url = image_url_map.get(fname, path)
                html.append(f'<figure class="wp-block-image"><img src="{wp_url}" alt="{escape_xml(alt)}" /></figure>')
        elif line.startswith("- "):
            if not in_ul: html.append("<ul>"); in_ul = True
            html.append(f"<li>{bold(line[2:])}</li>")
        elif line.startswith("|"):
            if in_ul: html.append("</ul>"); in_ul = False
            if not in_table:
                in_table = True; html.append("<table>")
                cells = [c.strip() for c in line.strip("|").split("|")]
                html.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr></thead><tbody>")
            elif re.match(r'^\|[-| ]+\|', line):
                pass
            else:
                cells = [c.strip() for c in line.strip("|").split("|")]
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        else:
            if in_table: html.append("</tbody></table>"); in_table = False
            if in_ul: html.append("</ul>"); in_ul = False
            if line.strip():
                html.append(f"<p>{link(bold(line.strip()))}</p>")

    if in_ul: html.append("</ul>")
    if in_table: html.append("</tbody></table>")
    return "\n".join(html)

def publish_post(title: str, content_html: str, thumbnail_id: str = "") -> str:
    thumbnail_xml = ""
    if thumbnail_id:
        thumbnail_xml = f"""
<member><name>custom_fields</name><value><array><data>
  <value><struct>
    <member><name>key</name><value><string>_thumbnail_id</string></value></member>
    <member><name>value</name><value><string>{thumbnail_id}</string></value></member>
  </struct></value>
</data></array></value></member>"""

    params = f"""
<param><value><int>1</int></value></param>
<param><value><string>{WP_USERNAME}</string></value></param>
<param><value><string>{WP_APP_PASSWORD}</string></value></param>
<param><value><struct>
  <member><name>post_title</name><value><string>{escape_xml(title)}</string></value></member>
  <member><name>post_content</name><value><string>{escape_xml(content_html)}</string></value></member>
  <member><name>post_status</name><value><string>publish</string></value></member>
  <member><name>post_type</name><value><string>post</string></value></member>
  {thumbnail_xml}
</struct></value></param>"""
    root = xmlrpc("wp.newPost", params)
    post_id = root.findtext(".//value/string") or root.findtext(".//value/int")
    return post_id

def parse_md(md_path: str) -> dict:
    text = Path(md_path).read_text(encoding="utf-8")
    title = ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else text
        m = re.search(r'^title:\s*(.+)$', parts[1], re.MULTILINE)
        title = m.group(1).strip() if m else ""
    else:
        body = text.strip()
    if not title:
        for line in body.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip(); break
    return {"title": title, "body": body}

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 wp_post.py <記事.md> [漫画.png] [バナー.png]")
        sys.exit(1)

    for var, name in [(WP_SITE_URL,"WP_SITE_URL"),(WP_USERNAME,"WP_USERNAME"),(WP_APP_PASSWORD,"WP_APP_PASSWORD")]:
        if not var:
            print(f"エラー: {name} が設定されていません")
            sys.exit(1)

    md_path = sys.argv[1]
    manga_path = sys.argv[2] if len(sys.argv) >= 3 else None
    banner_path = sys.argv[3] if len(sys.argv) >= 4 else None

    article = parse_md(md_path)
    print(f"タイトル: {article['title']}")

    # 画像をアップロード
    image_url_map = {}
    banner_id = ""

    # 本文内の画像を自動検出してアップロード
    img_paths = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', article["body"])
    for img_path in img_paths:
        if img_path.startswith("http"):
            continue
        full_path = img_path if Path(img_path).exists() else str(Path(md_path).parent.parent / img_path)
        if Path(full_path).exists():
            fname = Path(full_path).name
            print(f"  画像アップロード: {fname}")
            url, _ = upload_image(full_path, fname)
            image_url_map[fname] = url

    if manga_path and Path(manga_path).exists():
        print(f"  4コマ漫画アップロード: {Path(manga_path).name}")
        manga_url, _ = upload_image(manga_path, Path(manga_path).name)
        image_url_map[Path(manga_path).name] = manga_url

    if banner_path and Path(banner_path).exists():
        print(f"  バナーアップロード: {Path(banner_path).name}")
        banner_url, banner_id = upload_image(banner_path, Path(banner_path).name)
        image_url_map[Path(banner_path).name] = banner_url

    # HTML変換
    content_html = md_to_html(article["body"], image_url_map)

    # 4コマ漫画を冒頭に挿入
    if manga_path and Path(manga_path).name in image_url_map:
        manga_url = image_url_map[Path(manga_path).name]
        content_html = f'<figure class="wp-block-image"><img src="{manga_url}" alt="4コマ漫画" /></figure>\n' + content_html

    # 投稿
    print("WordPressに投稿中...")
    post_id = publish_post(article["title"], content_html, thumbnail_id=banner_id)
    url = f"{WP_SITE_URL}/?p={post_id}"
    print(f"\n✓ 投稿完了！")
    print(f"URL: {url}")
    return url

if __name__ == "__main__":
    main()
