#!/usr/bin/env python3
"""Fetch YouTube page (or load saved HTML) and extract the video description.

Usage:
  python scripts/fetch_youtube_desc_local.py --url "https://m.youtube.com/watch?v=..."
  python scripts/fetch_youtube_desc_local.py --file /path/to/saved_page.html

The script will attempt the same extraction strategy as the project's view:
- extract `attributedDescriptionBodyText` JSON object if present
- fallback to `ytInitialPlayerResponse -> videoDetails.shortDescription`

Output: prints HTML-safe description with clickable links and basic handle->URL conversion.
"""
import argparse
import re
import json
import html as _html
import sys

try:
    import requests
except Exception:
    requests = None


def load_html_from_url(url, timeout=10):
    if requests is None:
        raise RuntimeError('requests not available; install requests to fetch URLs')
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text


def load_html_from_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()


def extract_attributed_description(html):
    idx = html.find('"attributedDescriptionBodyText"')
    if idx == -1:
        return None
    obj_start = html.find('{', idx)
    if obj_start == -1:
        return None
    depth = 0
    end = None
    for i in range(obj_start, len(html)):
        if html[i] == '{':
            depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return None
    json_text = html[obj_start:end+1]
    try:
        obj = json.loads(json_text)
        if isinstance(obj, dict) and 'content' in obj:
            return obj.get('content')
    except Exception:
        return None
    return None


def extract_short_description(html):
    m_init = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;', html, flags=re.DOTALL)
    if not m_init:
        return None
    try:
        ipr = json.loads(m_init.group(1))
        vd = ipr.get('videoDetails', {})
        short = vd.get('shortDescription')
        return short
    except Exception:
        return None


def linkify(text):
    if not text:
        return text
    # unescape non-breaking spaces
    text = text.replace('\u00a0', ' ')

    # convert plain URLs to anchors
    def _url_repl(m):
        url = m.group(0)
        # Heuristic: if an uppercase-starting word (e.g. 'Follow') was concatenated
        # to the URL path without whitespace, split it off so it's not part of the anchor.
        for i in range(len(url)):
            if i > 0 and url[i].isupper() and url[i-1] == '/':
                anchor = url[:i]
                leftover = url[i:]
                return f'<a href="{anchor}" target="_blank" rel="noopener noreferrer">{anchor}</a>' + leftover
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'

    text = re.sub(r'(https?://[^\s<]+)', _url_repl, text)

    # convert @handles for TikTok/Instagram to full URLs (common patterns)
    # e.g. @cleansoundst -> https://www.tiktok.com/@cleansoundst
    def _handle_repl(m):
        handle = m.group('h')
        # default to TikTok if preceded by 'tiktok' in nearby text? keep simple: provide both links
        tt = f'<a href="https://www.tiktok.com/@{handle}" target="_blank" rel="noopener noreferrer">@{handle}</a>'
        ig = f'<a href="https://www.instagram.com/{handle}/" target="_blank" rel="noopener noreferrer">@{handle}</a>'
        # return both separated by space so user can choose
        return tt + ' ' + ig

    text = re.sub(r'@(?P<h>[A-Za-z0-9_.-]{2,30})', _handle_repl, text)

    # convert naked 'instagram.com/...' or 'tiktok.com/...' already handled by URL regex
    # preserve line breaks as <br>
    text = text.replace('\n', '<br>')
    return text


def extract_description_from_html(html):
    # Prefer meta description in the <head> when available (matches YouTube's
    # <meta name="description" content="..."> or <meta property="og:description" ...>).)
    desc = None
    try:
        for m in re.finditer(r'<meta\b([^>]*)>', html, flags=re.IGNORECASE | re.DOTALL):
            attrs = m.group(1)
            name_m = re.search(r'\b(?:name|property)\s*=\s*["\']([^"\']+)["\']', attrs, flags=re.I)
            if name_m:
                key = name_m.group(1).lower()
                if key in ('description', 'og:description'):
                    content_m = re.search(r'\bcontent\s*=\s*["\']([^"\']*)["\']', attrs, flags=re.I)
                    if content_m:
                        desc = content_m.group(1)
                        break
    except Exception:
        desc = None

    if not desc:
        desc = extract_attributed_description(html)
    if not desc:
        desc = extract_short_description(html)
    return desc


def main():
    p = argparse.ArgumentParser(description='Extract YouTube description from HTML or URL')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', help='YouTube watch URL (eg https://m.youtube.com/watch?v=...)')
    group.add_argument('--file', help='Path to saved HTML file')
    args = p.parse_args()

    try:
        if args.url:
            html = load_html_from_url(args.url)
        else:
            html = load_html_from_file(args.file)
    except Exception as e:
        print('Failed to load HTML:', e, file=sys.stderr)
        sys.exit(2)

    desc = extract_description_from_html(html)
    if not desc:
        print('Description not found', file=sys.stderr)
        sys.exit(3)
    # Normalize escaped newline sequences and unescape HTML entities that may
    # be present in the extracted meta/JS string. This prevents literal '\\n'
    # from being treated as part of a URL by the link regex.
    try:
        desc = desc.replace('\\n', '\n').replace('\\r', '\r')
        desc = _html.unescape(desc)
    except Exception:
        pass

    html_desc = linkify(desc)
    print(html_desc)


if __name__ == '__main__':
    main()
