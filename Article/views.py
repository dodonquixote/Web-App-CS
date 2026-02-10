from django.shortcuts import render
from django.shortcuts import get_object_or_404
from DashboardAdmin.models import Article as DashboardArticle, SiteSetting, ArticleTranslation, SiteSettingTranslation
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.text import Truncator
from django.utils.html import strip_tags
# Needed for HTML-safe fallback in API snippets
from django.utils.safestring import mark_safe
from django.utils.html import escape
# reuse formatting helper for API HTML snippets
from Article.templatetags.embed_filters import format_youtube_desc, autoembed
import re
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
import hashlib
import logging
import concurrent.futures
import uuid

try:
    import requests
except Exception:
    requests = None
from django.core.cache import cache


logger = logging.getLogger(__name__)


def _normalize_lang(value, fallback='id'):
    lang = (value or fallback or 'id').lower()
    if lang == 'jp':
        lang = 'ja'
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return lang


def _shield_embeds(html):
    """Cache iframe/embed HTML server-side and replace with safe text tokens.

    Returns (masked_html, list_of_cache_keys).
    Token format: %%CS_EMBED_<hex>%% where cache key is 'cs_embed_<hex>'.
    """
    if not html:
        return html, []
    keys = []

    def _repl(m):
        original = m.group(0)
        uid = uuid.uuid4().hex
        key = f'cs_embed_{uid}'
        try:
            # store original HTML in Django cache for later restore
            cache.set(key, original, 60 * 60 * 24)  # 24h
        except Exception:
            pass
        keys.append(key)
        # use a custom lightweight tag placeholder that will be preserved as a tag
        # example: <cs-embed data-cs-embed="cs_embed_abcdef1234"></cs-embed>
        token = f'<cs-embed data-cs-embed="{key}"></cs-embed>'
        return token

    # First capture wrapper blocks that contain an iframe (e.g., <div>...<iframe>...</iframe></div>),
    # so we replace the whole wrapper to avoid leaving stray wrapper markup around restored iframe.
    wrapper_pattern = re.compile(r'(<(?:div|figure|p)[^>]*>\s*(?:<iframe[\s\S]*?>[\s\S]*?<\/iframe>)\s*<\/(?:div|figure|p)>)', flags=re.I)
    masked = wrapper_pattern.sub(_repl, html)
    # then replace standalone iframe blocks
    masked = re.sub(r'(<iframe[\s\S]*?>[\s\S]*?<\/iframe>)', _repl, masked, flags=re.I)
    # replace embed tags
    masked = re.sub(r'(<embed[\s\S]*?\/?>)', _repl, masked, flags=re.I)
    return masked, keys


def _restore_placeholders(text, placeholders):
    if not text:
        return text

    # Replace custom tag placeholders like <cs-embed data-cs-embed="cs_embed_<hex>"></cs-embed>
    # Also try variations in case the placeholder format changed
    def _repl_token(m):
        key = m.group('key')
        try:
            orig = cache.get(key)
            if orig:
                try:
                    cache.delete(key)
                except Exception:
                    pass
                return orig
        except Exception:
            pass
        
        # If cache miss, return the original placeholder
        # This is better than losing content
        return m.group(0)

    # Match <cs-embed ... data-cs-embed="KEY" ...> with optional closing tag
    pattern = re.compile(
        r'<cs-embed\s+[^>]*data-cs-embed=["\'](?P<key>cs_[a-z0-9_]+)["\'][^>]*>(?:\s*<\/cs-embed>\s*)?',
        flags=re.I | re.DOTALL
    )
    
    result = pattern.sub(_repl_token, text)
    return result


def _shield_youtube_links(html):
    """Replace plain YouTube URLs in text with cache-backed placeholders.

    This prevents translation providers from converting URLs into HTML or
    otherwise mangling them. Returns (masked_html, list_of_cache_keys).
    """
    if not html:
        return html, []

    keys = []
    # pattern covers watch?v=, youtu.be/, and embed/ links
    # Now captures trailing parameters like ?si=... or &list=... etc.
    url_pattern = re.compile(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([A-Za-z0-9_-]{6,})(?:[^\s<>"]*)?)', flags=re.I)

    def _repl(m):
        original_url = m.group(1)
        vid = m.group(2)
        uid = uuid.uuid4().hex
        key = f'cs_embed_{uid}'
        # Store the ORIGINAL URL, not converted to iframe
        # This preserves the original article structure
        try:
            cache.set(key, original_url, 60 * 60 * 24)
        except Exception:
            pass
        keys.append(key)
        return f'<cs-embed data-cs-embed="{key}"></cs-embed>'

    # Only replace URLs that appear in text nodes, not within tags
    parts = re.split(r'(<[^>]+>)', html)
    for i, p in enumerate(parts):
        if p.startswith('<'):
            continue
        parts[i] = url_pattern.sub(_repl, p)

    return ''.join(parts), keys


def coba(request):
    return render(request, 'coba.html')

def test_translation(request):
    """Test page for translation flow"""
    return render(request, 'test_translation.html')

# Create your views here.
def article(request, lang=None):
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return render(request, 'article.html', {'current_language': lang})

def home(request, lang=None):
    # Get language from URL parameter or use request language
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    
    setting = SiteSetting.get_solo()

    # normalize youtube link to an embed URL so iframe loads the player correctly
    def to_embed_url(url):
        if not url:
            return ''
        # try to extract video id from common youtube url patterns
        m = None
        # watch?v=VIDEO or &v=VIDEO
        m = re.search(r'[?&]v=([A-Za-z0-9_-]{6,})', url)
        if not m:
            # youtu.be/VIDEO or youtube.com/embed/VIDEO
            m = re.search(r'(?:youtu\.be/|/embed/)([A-Za-z0-9_-]{6,})', url)
        if m:
            vid = m.group(1)
            return f'https://www.youtube.com/embed/{vid}'
        # if already looks like embed or raw id
        if re.match(r'^[A-Za-z0-9_-]{6,}$', url):
            return f'https://www.youtube.com/embed/{url}'
        if 'youtube.com/embed/' in url:
            return url
        # fallback: return original
        return url

    youtube_embed = to_embed_url(setting.youtube_link)

    youtube_desc = setting.youtube_desc
    if lang != 'id':
        try:
            t = SiteSettingTranslation.objects.filter(setting=setting, lang=lang).first()
        except Exception:
            t = None
        if t and t.youtube_desc:
            youtube_desc = t.youtube_desc

    return render(request, 'index.html', {
        'spotify_link': setting.spotify_link,
        'youtube_link': setting.youtube_link,
        'youtube_embed': youtube_embed,
        'youtube_desc': youtube_desc,
        'vote_link': getattr(setting, 'vote_link', ''),
        'current_language': lang,
    })

def anime(request, lang=None):
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return render(request, 'anime.html', {'current_language': lang})

def event(request, lang=None):
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return render(request, 'event.html', {'current_language': lang})

def game(request, lang=None):
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return render(request, 'game.html', {'current_language': lang})

def geek(request, lang=None):
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    return render(request, 'geek.html', {'current_language': lang})


def article_detail(request, slug, lang=None):
    # Get language from URL parameter or use request language
    if lang is None:
        lang = getattr(request, 'language', 'id')
    if lang == 'jp':
        lang = 'ja'
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    if lang not in ['id', 'en', 'ja']:
        lang = 'id'
    
    article = get_object_or_404(DashboardArticle, slug=slug, status='published')
    
    # Get translated content if language is not Indonesian
    content = article.content
    title = article.title
    if lang != 'id':
        try:
            translation = ArticleTranslation.objects.get(article=article, lang=lang)
            title = translation.title
            content = translation.content
        except ArticleTranslation.DoesNotExist:
            # Fall back to Indonesian if translation doesn't exist
            lang = 'id'
    
    # Apply autoembed filter to convert YouTube URLs to iframes
    from Article.templatetags.embed_filters import autoembed
    content = autoembed(content)
    
    # Include site-wide settings (ads, youtube, etc.) so templates can render them
    try:
        setting = SiteSetting.get_solo()
    except Exception:
        setting = None

    # compute accessible URLs for ad images (use absolute URIs to avoid relative/media issues)
    ad_left_url = None
    ad_right_url = None
    ad_down_url = None
    ad_top_url = None
    ad_left_link = None
    ad_right_link = None
    ad_top_link = None
    ad_down_link = None
    
    if setting:
        try:
            if setting.ad_left:
                ad_left_url = request.build_absolute_uri(setting.ad_left.url)
                ad_left_link = setting.ad_left_link or None
        except Exception:
            pass
        
        try:
            if setting.ad_right:
                ad_right_url = request.build_absolute_uri(setting.ad_right.url)
                ad_right_link = setting.ad_right_link or None
        except Exception:
            pass
        
        try:
            if setting.ad_down:
                ad_down_url = request.build_absolute_uri(setting.ad_down.url)
                ad_down_link = setting.ad_down_link or None
        except Exception:
            pass
        
        try:
            if setting.ad_top:
                ad_top_url = request.build_absolute_uri(setting.ad_top.url)
                ad_top_link = setting.ad_top_link or None
        except Exception:
            pass

    return render(request, 'article.html', {
        'article': article,
        'title': title,
        'content': content,
        'current_language': lang,
        'setting': setting,
        'ad_left_url': ad_left_url,
        'ad_right_url': ad_right_url,
        'ad_down_url': ad_down_url,
        'ad_top_url': ad_top_url,
        'ad_left_link': ad_left_link,
        'ad_right_link': ad_right_link,
        'ad_top_link': ad_top_link,
        'ad_down_link': ad_down_link,
    })


@require_GET
def api_articles_by_category(request, category_name):
    """Return published articles for a category as JSON, paginated.

    Query params:
      - page (int): 1-based page number (default 1)
      - page_size (int): items per page (default 10)

    Response JSON:
      { items: [...], page: n, total_pages: m, total_items: t, page_size: s }
    """
    # Determine language from query or middleware
    lang = _normalize_lang(request.GET.get('lang') or getattr(request, 'language', 'id'))
    prefix = '' if lang == 'id' else f'/{lang}'
    
    logger.info(f'[api_articles_by_category] category={category_name}, lang={lang}, prefix={prefix}')

    # Prefer pinned articles first so frontend can render a pinned hero
    qs = DashboardArticle.objects.filter(category__name__iexact=category_name, status='published').order_by('-is_pinned', '-published_at', '-created_at')
    
    logger.info(f'[api_articles_by_category] Found {qs.count()} articles for category {category_name}')

    # parse paging parameters
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', '10'))
        if page_size < 1:
            page_size = 10
    except Exception:
        page_size = 10

    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    data = []

    translations_map = {}
    if lang != 'id':
        # Avoid MySQL limitation with LIMIT + IN subquery by materializing IDs
        article_ids = list(page_obj.object_list.values_list('id', flat=True))
        translations = ArticleTranslation.objects.filter(article_id__in=article_ids, lang=lang)
        translations_map = {t.article_id: t for t in translations}
        logger.info(f'[api_articles_by_category] Found {len(translations_map)} translations for lang={lang}')
    
    for a in page_obj.object_list:
        if a.featured_image and hasattr(a.featured_image, 'url'):
            try:
                img_url = request.build_absolute_uri(a.featured_image.url)
            except Exception:
                img_url = a.featured_image.url
        else:
            img_url = '/static/images/placeholder.png'

        t = translations_map.get(a.id)
        title = t.title if t and t.title else a.title
        raw = t.content if t and t.content else (a.content or '')

        # Prepare a short plain-text description without leading images
        # remove a leading <p> or <figure> that contains an <img> (optionally wrapped in <a>)
        raw_no_leading_img = re.sub(r'^(?:\s*<(?:p|figure)[^>]*>\s*)?(?:<a[^>]*>\s*)?(?:<img[^>]*>)(?:\s*</a>)?(?:\s*</(?:p|figure)>)?', '', raw, flags=re.I)
        # strip remaining HTML tags and collapse whitespace
        plain = strip_tags(raw_no_leading_img).strip()
        plain = re.sub(r'\s+', ' ', plain)
        short_desc = Truncator(plain).chars(150)
        # also provide an HTML-friendly snippet that preserves links and
        # converts literal/newline separators into <p>/<br> for clients
        try:
            desc_html = format_youtube_desc(raw_no_leading_img)
        except Exception:
            # fallback: escape and convert newlines
            desc_html = mark_safe(escape(raw_no_leading_img).replace('\n', '<br>'))

        data.append({
            'id': a.id,
            'title': title,
            'slug': a.slug,
            'url': (request.build_absolute_uri(f'{prefix}/article/{a.slug}/') if a.slug else None),
            'category': a.category.name if a.category else '',
            'img': img_url,
            'desc': short_desc,
            'desc_html': desc_html,
            'is_pinned': bool(a.is_pinned),
        })
    
    logger.info(f'[api_articles_by_category] Returning {len(data)} items')

    return JsonResponse({
        'items': data,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_items': paginator.count,
        'page_size': page_size,
    })


@require_GET
def api_pinned_article(request, category_name):
    """Return the first published pinned article for a category, or null.

    Response: { item: {...} } or { item: null }
    """
    lang = _normalize_lang(request.GET.get('lang') or getattr(request, 'language', 'id'))
    prefix = '' if lang == 'id' else f'/{lang}'

    try:
        a = DashboardArticle.objects.filter(category__name__iexact=category_name, status='published', is_pinned=True).order_by('-published_at', '-created_at').first()
    except Exception:
        a = None

    if not a:
        return JsonResponse({'item': None})

    if a.featured_image and hasattr(a.featured_image, 'url'):
        try:
            img_url = request.build_absolute_uri(a.featured_image.url)
        except Exception:
            img_url = a.featured_image.url
    else:
        img_url = '/static/images/placeholder.png'

    t = None
    if lang != 'id':
        try:
            t = ArticleTranslation.objects.get(article=a, lang=lang)
        except ArticleTranslation.DoesNotExist:
            t = None

    title = t.title if t and t.title else a.title
    raw = t.content if t and t.content else (a.content or '')
    raw_no_leading_img = re.sub(r'^(?:\s*<(?:p|figure)[^>]*>\s*)?(?:<a[^>]*>\s*)?(?:<img[^>]*>)(?:\s*</a>)?(?:\s*</(?:p|figure)>)?', '', raw, flags=re.I)
    plain = strip_tags(raw_no_leading_img).strip()
    plain = re.sub(r'\s+', ' ', plain)
    short_desc = Truncator(plain).chars(150)
    try:
        desc_html = format_youtube_desc(raw_no_leading_img)
    except Exception:
        from django.utils.safestring import mark_safe
        from django.utils.html import escape
        desc_html = mark_safe(escape(raw_no_leading_img).replace('\n', '<br>'))

    item = {
        'id': a.id,
        'title': title,
        'slug': a.slug,
        'url': (request.build_absolute_uri(f'{prefix}/article/{a.slug}/') if a.slug else None),
        'category': a.category.name if a.category else '',
        'img': img_url,
        'desc': short_desc,
        'desc_html': desc_html,
        'is_pinned': True,
    }

    return JsonResponse({'item': item})


def _translate_text_via_provider(text, target_lang, source_lang='auto'):
    """Translate `text` to `target_lang` using configured provider.

    By default this uses LibreTranslate public instance at https://libretranslate.com/translate
    Configure `TRANSLATE_API_URL` and `TRANSLATE_API_KEY` environment variables to use another provider.
    """
    logger = logging.getLogger(__name__)

    if not requests:
        logger.error('requests library is not available for translation provider')
        raise RuntimeError('requests library is required for translation provider')

    # cache key: sha256 of text + target lang
    try:
        cache_ttl = int(os.environ.get('TRANSLATION_CACHE_TTL', '86400'))
    except Exception:
        cache_ttl = 86400
    key_hash = hashlib.sha256((text or '').encode('utf-8')).hexdigest()
    target_norm = (target_lang or '').lower()
    source_norm = (source_lang or 'auto').lower()
    cache_key = 'translation:{}:{}:{}'.format(key_hash, source_norm, target_norm)
    try:
        cached = cache.get(cache_key)
    except Exception:
        cached = None
    if cached:
        return cached

    # map commonly-used client language codes to provider expected codes
    LANG_MAP = {
        'jp': 'ja',  # user-facing used 'jp' -> provider expects 'ja'
        'ja': 'ja',
        'id': 'id',
        'in': 'id',
        'en': 'en'
    }
    mapped_target = LANG_MAP.get((target_lang or '').lower(), target_lang)

    # Prefer explicit environment variable, then SiteSetting value, then local default
    url = os.environ.get('TRANSLATE_API_URL', '')
    api_key = os.environ.get('TRANSLATE_API_KEY', '')
    if not url:
        try:
            setting = SiteSetting.get_solo()
            url = (setting.translate_api_url or '').strip()
            if not api_key:
                api_key = (setting.translate_api_key or '').strip()
        except Exception:
            url = ''
    if not url:
        url = 'http://127.0.0.1:5000/translate'

    # Prepare payload (caller is responsible for shielding HTML/embed blocks when needed)
    payload = {
        'q': text,
        'source': (source_lang or 'auto'),
        'target': mapped_target,
        'format': 'html'
    }
    if api_key:
        payload['api_key'] = api_key

    headers = {'Content-Type': 'application/json'}

    # Configure session with retries and backoff to tolerate transient provider issues
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=frozenset(['GET', 'POST']))
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
    except Exception:
        # fallback to requests.post directly
        session = requests

    try:
        # increase timeout to handle provider model loading or slow responses
        resp = session.post(url, json=payload, headers=headers, timeout=60)
        # if session is requests module, resp may be a Response or an exception will be raised
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # try to include response body when available
        body = None
        try:
            if 'resp' in locals() and resp is not None:
                body = getattr(resp, 'text', None)
        except Exception:
            body = None
        
        # PIVOT TRANSLATION: Indonesian source tidak support langsung ke en/ja
        # Solusi: Gunakan English sebagai bahasa perantara
        # id -> en (via auto-detect to English) atau id -> en -> ja
        if body and 'not available as a target language' in str(body):
            # Cek apakah ini masalah Indonesian source language
            if 'Indonesian' in str(body) or source_norm == 'id':
                try:
                    if target_norm == 'en':
                        # Untuk target English: coba translate dari auto ke English
                        # (kadang LibreTranslate butuh source='auto' bukan 'id')
                        logger.info(f'Retrying translation with source=auto for target=en')
                        payload_retry = payload.copy()
                        payload_retry['source'] = 'auto'
                        resp_retry = session.post(url, json=payload_retry, headers=headers, timeout=60)
                        resp_retry.raise_for_status()
                        data = resp_retry.json()
                        # Jika berhasil, lanjut ke parsing result
                    elif target_norm in ['ja', 'jp']:
                        # Untuk target Japanese: pivot melalui English
                        logger.info(f'Pivoting translation: Indonesian -> English -> Japanese')
                        # Step 1: Indonesian -> English
                        intermediate = _translate_text_via_provider(text, 'en', source_lang='auto')
                        # Step 2: English -> Japanese
                        result_text = _translate_text_via_provider(intermediate, 'ja', source_lang='en')
                        # Cache result
                        try:
                            cache.set(cache_key, result_text, cache_ttl)
                        except Exception:
                            pass
                        return result_text
                    else:
                        raise RuntimeError(f"provider_request_failed: {e}; body={body}")
                except Exception as pivot_error:
                    logger.error(f'Pivot translation failed: {pivot_error}')
                    raise RuntimeError(f"provider_request_failed: {e}; body={body}")
            else:
                raise RuntimeError(f"provider_request_failed: {e}; body={body}")
        else:
            logger.exception('Translation provider request failed')
            raise RuntimeError(f"provider_request_failed: {e}; body={body}")

    # derive final text
    result_text = None
    if isinstance(data, dict) and 'translatedText' in data:
        result_text = data['translatedText']
    elif isinstance(data, dict) and 'translation' in data:
        result_text = data['translation']
    elif isinstance(data, dict) and 'translated' in data:
        # some endpoints return {translated: '...'}
        result_text = data['translated']
    else:
        result_text = str(data)

    # Note: callers should restore placeholders when they performed shielding.

    # cache result if possible
    try:
        cache.set(cache_key, result_text, cache_ttl)
    except Exception:
        pass

    return result_text


def _translate_html_preserve_tags(html, target_lang, chunk_size=3000):
    """Translate only text nodes in `html` while preserving tags (iframes, embeds, attributes).

    This splits the HTML into tags and text, batches text segments, sends them to the provider,
    and stitches translated text back into place. This avoids the provider touching iframe tags.
    """
    if not html:
        return html

    # Shield plain YouTube links and embed/iframe blocks server-side by replacing
    # them with cache-backed placeholders. Shielding plain URLs first prevents
    # the provider from converting URLs into HTML (which caused nested/malformed
    # iframe markup previously).
    masked_html, y_keys = _shield_youtube_links(html)
    masked_html, e_keys = _shield_embeds(masked_html)
    placeholders = (y_keys or []) + (e_keys or [])
    # operate on masked HTML for translation
    html = masked_html

    # split into tags and text
    parts = re.split(r'(<[^>]+>)', html)
    # indices of text parts
    text_indices = [i for i, p in enumerate(parts) if not p.startswith('<')]
    if not text_indices:
        return html

    translated_parts = parts[:]  # copy

    # Translate text parts individually to avoid provider mangling of delimiters.
    # Use a small thread pool to parallelize but avoid flooding the provider.
    to_translate = []
    for idx in text_indices:
        if parts[idx].strip():
            to_translate.append((idx, parts[idx]))
        else:
            # keep whitespace-only segments as-is
            translated_parts[idx] = parts[idx]

    if to_translate:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
                futures = {ex.submit(_translate_text_via_provider, text, target_lang): idx for idx, text in to_translate}
                for fut in concurrent.futures.as_completed(futures):
                    idx = futures[fut]
                    try:
                        translated_parts[idx] = fut.result()
                    except Exception:
                        # on failure, keep original segment
                        pass
        except Exception:
            # fallback: leave original parts
            pass

    result = ''.join(translated_parts)
    # restore any embed placeholders back to original HTML from cache
    try:
        result = _restore_placeholders(result, placeholders)
    except Exception:
        pass

    # NOTE: Do not normalize plain YouTube links into iframe embeds here.
    # Converting links -> iframe during translation has previously caused
    # nested/duplicated iframe HTML in some articles. Leave original HTML
    # structure intact and let the frontend/template logic handle embeds.
    return result


def _normalize_youtube_links_to_iframe(html):
    """Replace plain YouTube watch/watch?v= or youtu.be links in text with iframe embed HTML."""
    if not html:
        return html
    # If the HTML already contains an iframe or an embed placeholder, skip normalization
    # to avoid creating nested or duplicated iframe markup.
    low = html.lower()
    if '<iframe' in low or '&lt;iframe' in low or '<cs-embed' in low:
        return html
    
    def _repl_watch(m):
        vid = m.group('id')
        iframe = f'<div class="w-full aspect-video mb-6"><iframe src="https://www.youtube.com/embed/{vid}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
        return iframe

    # Only replace URLs that appear in text nodes (not inside HTML tag attributes).
    parts = re.split(r'(<[^>]+>)', html)
    for i, p in enumerate(parts):
        # skip tags
        if p.startswith('<'):
            continue
        # Combine all three URL patterns into one regex with alternation
        # This prevents the third pattern from matching URLs created by earlier replacements
        combined_pattern = (
            r'https?://(?:www\.)?youtube\.com/watch\?v=(?P<id>[A-Za-z0-9_-]{6,})[^\s<"\)]*'
            r'|https?://(?:www\.)?youtu\.be/(?P<id2>[A-Za-z0-9_-]{6,})[^\s<"\)]*'
            r'|https?://(?:www\.)?youtube\.com/embed/(?P<id3>[A-Za-z0-9_-]{6,})[^\s<"\)]*'
        )
        
        def _repl_combined(m):
            # Extract the video ID from whichever group matched
            vid = m.group('id') or m.group('id2') or m.group('id3')
            iframe = f'<div class="w-full aspect-video mb-6"><iframe src="https://www.youtube.com/embed/{vid}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>'
            return iframe
        
        p = re.sub(combined_pattern, _repl_combined, p, flags=re.I)
        parts[i] = p
    return ''.join(parts)


def _unwrap_iframe_from_links(html):
    """Remove invalid link wrappers around iframes and cs-embed placeholders."""
    if not html:
        return html
    
    # Remove anchor tags that wrap iframe/cs-embed blocks
    # Pattern 1: <a>...<strong>...<div><iframe/></div>...</strong>...</a>
    pattern1 = re.compile(
        r'<a\b[^>]*>\s*(?:<strong[^>]*>\s*)?(?P<block><div[^>]*>\s*(?:<iframe[\s\S]*?>[\s\S]*?<\/iframe>|<cs-embed[^>]*>(?:<\/cs-embed>)?)\s*<\/div>)\s*(?:<\/strong>)?\s*<\/a>',
        flags=re.I,
    )
    html = pattern1.sub(lambda m: m.group('block'), html)
    
    # Pattern 2: <a>...<cs-embed/></a> (direct cs-embed in anchor without div)
    pattern2 = re.compile(
        r'<a\b[^>]*>\s*(?:<strong[^>]*>\s*)?(?P<block><cs-embed[^>]*>(?:<\/cs-embed>)?)\s*(?:<\/strong>)?\s*<\/a>',
        flags=re.I,
    )
    html = pattern2.sub(lambda m: m.group('block'), html)
    
    return html


@csrf_exempt
@require_POST
def api_translate(request):
    """Translate a page or text.

    POST JSON body examples:
    - Translate an article by slug:
      { "page": "article", "slug": "some-article-slug", "lang": "en" }

    - Translate arbitrary HTML/text:
      { "page": "html", "content": "<p>...</p>", "lang": "jp" }

    Response: JSON with translated fields or error.
    """
    if request.content_type != 'application/json':
        # allow application/json or other; try to parse body anyway
        pass
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    lang = body.get('lang')
    if not lang:
        return JsonResponse({'error': 'lang_required'}, status=400)

    # normalize language codes
    if lang == 'jp':
        lang = 'ja'


    page_type = body.get('page')
    if page_type == 'article':
        slug = body.get('slug')
        if not slug:
            return JsonResponse({'error': 'slug_required'}, status=400)
        try:
            article = DashboardArticle.objects.get(slug=slug, status='published')
        except DashboardArticle.DoesNotExist:
            return JsonResponse({'error': 'not_found'}, status=404)

        # Use only pre-translated content stored at save-time
        try:
            stored = ArticleTranslation.objects.filter(article=article, lang=lang).first()
        except Exception:
            stored = None
        if stored:
            # Apply autoembed filter to convert plain YouTube URLs to iframes
            content_with_embeds = autoembed(stored.content)
            return JsonResponse({'title': stored.title, 'content': content_with_embeds, 'desc': stored.desc, 'lang': lang})

        if lang == 'id':
            # Apply autoembed filter to original content
            content_with_embeds = autoembed(article.content)
            return JsonResponse({'title': article.title, 'content': content_with_embeds, 'desc': Truncator(article.content).chars(150), 'lang': lang})

        return JsonResponse({'error': 'translation_not_ready', 'details': 'Translation not available. Save/publish the article to generate translations.'}, status=404)

    elif page_type == 'html':
        return JsonResponse({'error': 'unsupported_page_type', 'details': 'HTML translation is disabled. Use stored article translations.'}, status=400)

    else:
        return JsonResponse({'error': 'unsupported_page_type'}, status=400)


@require_GET
def api_article_detail(request, slug):
    """Return a single published article by slug as JSON.

    URL: /api/article/<slug>/
    """
    try:
        a = DashboardArticle.objects.get(slug=slug, status='published')
    except DashboardArticle.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    if a.featured_image and hasattr(a.featured_image, 'url'):
        try:
            img_url = request.build_absolute_uri(a.featured_image.url)
        except Exception:
            img_url = a.featured_image.url
    else:
        img_url = '/static/images/placeholder.png'

    return JsonResponse({
        'id': a.id,
        'title': a.title,
        'slug': a.slug,
        # Provide plain-text content by default to avoid returning raw HTML.
        # Keep original HTML available in `content_html` for clients that need it.
        'content_html': a.content,
        'content': re.sub(r'\s+', ' ', strip_tags(re.sub(r'^(?:\s*<(?:p|figure)[^>]*>\s*)?(?:<a[^>]*>\s*)?(?:<img[^>]*>)(?:\s*</a>)?(?:\s*</(?:p|figure)>)?', '', (a.content or ''), flags=re.I)).strip()),
        'url': (request.build_absolute_uri(f'/article/{a.slug}/') if a.slug else None),
        'category': a.category.name if a.category else '',
        'img': img_url,
        'published_at': a.published_at.isoformat() if a.published_at else None,
    })


def custom_404(request, exception=None):
    """Render a friendly 404 page using the app's not-found template.

    Note: Django only uses this when `DEBUG = False`. For local testing,
    set DEBUG=False or call this view directly.
    """
    return render(request, 'not-found.html', status=404)
