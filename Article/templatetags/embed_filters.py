from django import template
from django.utils.safestring import mark_safe
import re
from django.utils.html import escape

register = template.Library()


@register.filter(name='autoembed')
def autoembed(value):
    """Replace bare YouTube URLs in the given HTML/text with responsive iframe embed markup.

    Handles URLs like:
    - https://www.youtube.com/watch?v=VIDEOID
    - https://youtu.be/VIDEOID
    - https://www.youtube.com/embed/VIDEOID

    Does not modify existing <iframe> tags.
    """
    if not value:
        return value

    text = str(value)
    # If the stored text contains literal backslash-n sequences (e.g. "\\n"),
    # convert them to real newlines so we can turn them into <br> / <p> later.
    # This handles cases where JSON-escaped newlines or DB-escaped strings
    # were stored as two-character sequences rather than as actual newlines.
    text = text.replace('\\r\\n', '\n').replace('\\n', '\n')

    # If there's already an iframe, assume embeds are present; still try to convert plain URLs.
    # Regex to find YouTube video IDs in common URL patterns
    # Now captures trailing parameters like ?si=... or &list=... etc.
    pattern = re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{6,})(?:[^\s<>"]*)?', re.IGNORECASE)

    def repl(match):
        vid = match.group(1)
        # Try youtube-nocookie.com which sometimes works better
        iframe = (
            f'<div class="w-full mb-6" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;">'
            f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
            f'style="position:absolute;top:0;left:0;width:100%;height:100%;" '
            f'title="YouTube video player" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" '
            f'allowfullscreen></iframe></div>'
        )
        return iframe

    # Replace plain URLs only in text nodes (avoid altering existing tag attributes).
    parts = re.split(r'(<[^>]+>)', text)
    for i, p in enumerate(parts):
        # only operate on text segments (not tags)
        if p.startswith('<'):
            continue
        parts[i] = pattern.sub(repl, p)

    return mark_safe(''.join(parts))


@register.filter(name='format_youtube_desc')
def format_youtube_desc(value):
    """Clean and format YouTube description text for homepage display.

    - Replace slashes used as separators with newlines
    - Collapse excessive whitespace/newlines
    - Escape HTML and convert newlines to <br>
    """
    if not value:
        return value

    text = str(value)

    # Normalize non-breaking spaces and literal HTML entity '&nbsp;'
    # so pasted/copy-pasted descriptions don't show the entity in output.
    # Replace unicode NBSP and literal '&nbsp;' with a regular space.
    try:
        text = text.replace('\u00A0', ' ')
    except Exception:
        pass
    text = text.replace('&nbsp;', ' ')

    # Preserve any existing anchor tags by extracting them first so we don't
    # accidentally modify their contents (e.g. replace slashes in URLs).
    anchors = []

    def _anchor_repl(m):
        full = m.group(0)
        href_m = re.search(r'href\s*=\s*["\']([^"\']+)["\']', full, flags=re.I)
        href = href_m.group(1) if href_m else ''
        # Only allow http(s) or mailto links
        if not re.match(r'^(https?:|mailto:)', href, flags=re.I):
            return escape(full)
        # extract inner text (preserve content inside the tag)
        inner = re.sub(r'^<a[^>]*>|</a>$', '', full, flags=re.I | re.S)
        anchors.append((href, inner))
        return f'__ANCHOR_{len(anchors)-1}__'

    text_with_placeholders = re.sub(r'<a\b[^>]*>.*?<\/a>', _anchor_repl, text, flags=re.I | re.S)

    # Now operate on the remaining plain text: first protect plain URLs/emails
    # by replacing them with placeholders so subsequent slash normalization
    # does not split URLs into multiple lines.
    links = []

    def _link_repl(m):
        full = m.group(0)
        if re.match(r'^[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}$', full):
            href = f'mailto:{full}'
        else:
            href = full if re.match(r'^https?://', full, flags=re.I) else f'http://{full}'
        idx = len(links)
        links.append((href, full))
        return f'__LINK_{idx}__'

    text_with_placeholders = re.sub(r'(https?://[^\s<>]+|www\.[^\s<>]+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})', _link_repl, text_with_placeholders)

    # Now replace slashes used as separators (but URLs are protected), normalize whitespace,
    # trim, then convert newlines to <br>.
    text_with_placeholders = re.sub(r"\s*/\s*", "\n", text_with_placeholders)
    text_with_placeholders = re.sub(r"\r\n|\r", "\n", text_with_placeholders)
    text_with_placeholders = re.sub(r"[ \t]+", " ", text_with_placeholders)
    text_with_placeholders = re.sub(r"\n{3,}", "\n\n", text_with_placeholders)
    text_with_placeholders = text_with_placeholders.strip()

    # Convert double-newlines to paragraph breaks, single newline to <br>
    # First escape the text, then split into paragraphs
    esc = escape(text_with_placeholders)
    paragraphs = [p.strip() for p in esc.split('\n\n') if p.strip()]
    if paragraphs:
        para_html = []
        for p in paragraphs:
            p_html = p.replace('\n', '<br>')
            para_html.append(f'<p>{p_html}</p>')
        html = '\n'.join(para_html)
    else:
        html = esc.replace('\n', '<br>')

    # Reinsert sanitized anchors
    for idx, (href, inner) in enumerate(anchors):
        safe_href = escape(href)
        safe_inner = escape(inner)
        anchor_html = f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_inner}</a>'
        html = html.replace(f'__ANCHOR_{idx}__', anchor_html)

    # Reinsert linkified plain URLs/emails
    for idx, (href, inner) in enumerate(links):
        safe_href = escape(href)
        safe_inner = escape(inner)
        anchor_html = f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_inner}</a>'
        html = html.replace(f'__LINK_{idx}__', anchor_html)

    return mark_safe(html)
