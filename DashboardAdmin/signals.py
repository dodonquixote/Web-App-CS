import hashlib
import logging
import threading
import re

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.db import transaction, close_old_connections

from DashboardAdmin.models import Article, ArticleTranslation, SiteSetting, SiteSettingTranslation


logger = logging.getLogger(__name__)


def _source_hash(title, content):
    base = f"{title or ''}\n{content or ''}"
    return hashlib.sha256(base.encode('utf-8')).hexdigest()


@receiver(post_save, sender=Article)
def translate_article_on_save(sender, instance, **kwargs):
    logger.info(f'Signal triggered for article={instance.pk}, status={instance.status}')
    # Only translate published articles
    if instance.status != 'published':
        logger.info(f'Skipping translation - article not published')
        return

    source_hash = _source_hash(instance.title, instance.content)
    logger.info(f'Starting translation for article={instance.pk}, hash={source_hash[:8]}')

    def _run_translation(article_id, source_hash_value):
        close_old_connections()
        try:
            from Article.views import (
                _translate_text_via_provider,
                _translate_html_preserve_tags,
            )
        except Exception:
            logger.exception('Failed to import translation helpers')
            return

        try:
            article = Article.objects.get(pk=article_id)
        except Exception:
            return

        if article.status != 'published':
            return

        plain = strip_tags(article.content or '')
        base_desc = Truncator(plain).chars(150)

        for lang in ['id', 'en', 'ja']:
            try:
                existing = ArticleTranslation.objects.filter(article=article, lang=lang).first()
                if existing and existing.source_hash == source_hash_value:
                    continue

                if lang == 'id':
                    # Indonesian: use original content directly without any modification
                    title_t = article.title
                    content_t = article.content
                    desc_t = base_desc
                else:
                    # For English and Japanese: translate with split to preserve special patterns
                    # Split title to preserve quoted text and special patterns
                    title_parts = _split_text_and_preserve(article.title)
                    title_t = _translate_parts(title_parts, lang, _translate_text_via_provider)
                    
                    # Translate HTML content (shielding is done internally)
                    content_t = _translate_html_preserve_tags(article.content, lang)
                    
                    logger.info(f'Translation {lang}: {content_t.count("<iframe")} iframes found')
                    
                    desc_t = _translate_text_via_provider(base_desc, lang)

                if existing:
                    existing.title = title_t
                    existing.content = content_t
                    existing.desc = desc_t
                    existing.source_hash = source_hash_value
                    existing.save(update_fields=['title', 'content', 'desc', 'source_hash', 'updated_at'])
                else:
                    ArticleTranslation.objects.create(
                        article=article,
                        lang=lang,
                        title=title_t,
                        content=content_t,
                        desc=desc_t,
                        source_hash=source_hash_value,
                    )
                logger.info(f'Translation saved for {lang} article={article.pk}')
            except Exception:
                logger.exception('Translation failed for lang=%s article=%s', lang, article.pk)

        close_old_connections()

        close_old_connections()

    def _start_background():
        t = threading.Thread(
            target=_run_translation,
            args=(instance.pk, source_hash),
            daemon=True,
            name=f"translate-article-{instance.pk}",
        )
        t.start()

    transaction.on_commit(_start_background)

def _sitesetting_source_hash(youtube_desc):
    """Generate hash of youtube_desc for change detection."""
    return hashlib.sha256((youtube_desc or '').encode('utf-8')).hexdigest()


def _split_text_and_preserve(text):
    """Split text into parts: (is_preserved, content).
    
    Preserved parts are URLs, emails, phones, and newlines.
    Non-preserved parts are regular text that needs translation.
    """
    if not text:
        return []
    
    parts = []
    # Pattern: URLs, emails (strict - must have alphanumeric before @), phones, newlines
    # Email: alphanumeric.dash_percent before @, then domain.domain2.tld
    pattern = r'(https?://[^\s\n]+|[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+?\d[\d\s\-()]{6,}\d|\n\s*\n|\n)'
    last_end = 0
    
    for match in re.finditer(pattern, text):
        # Add text before this match (if any)
        if match.start() > last_end:
            parts.append((False, text[last_end:match.start()]))
        # Add the preserved part
        parts.append((True, match.group(0)))
        last_end = match.end()
    
    # Add remaining text
    if last_end < len(text):
        parts.append((False, text[last_end:]))
    
    return parts


def _translate_parts(parts, target_lang, translate_fn):
    """Translate only non-preserved parts, keep preserved parts unchanged."""
    result = []
    
    for is_preserved, content in parts:
        if is_preserved:
            # Keep as-is
            result.append(content)
        else:
            # Translate
            try:
                translated = translate_fn(content, target_lang)
                result.append(translated)
            except Exception as e:
                logger.warning(f'Translation failed for part, keeping original: {e}')
                result.append(content)
    
    return ''.join(result)



@receiver(post_save, sender=SiteSetting)
def translate_sitesetting_youtube_desc_on_save(sender, instance, **kwargs):
    """Translate YouTube description when SiteSetting is saved."""
    
    # Only proceed if youtube_desc is not empty
    if not instance.youtube_desc or not instance.youtube_desc.strip():
        return
    
    source_hash = _sitesetting_source_hash(instance.youtube_desc)

    def _run_translation(setting_id, source_hash_value):
        close_old_connections()
        try:
            from Article.views import _translate_text_via_provider
        except Exception:
            logger.exception('Failed to import translation helpers')
            return

        try:
            setting = SiteSetting.objects.get(pk=setting_id)
        except Exception:
            return

        # Check if we still have youtube_desc to translate
        if not setting.youtube_desc or not setting.youtube_desc.strip():
            return

        for lang in ['id', 'en', 'ja']:
            try:
                existing = SiteSettingTranslation.objects.filter(setting=setting, lang=lang).first()
                
                # Skip if unchanged (hash matches)
                if existing and existing.source_hash == source_hash_value:
                    continue

                if lang == 'id':
                    # Indonesian: use original content directly
                    desc_t = setting.youtube_desc
                else:
                    # For English and Japanese: split text and URLs, translate only text
                    parts = _split_text_and_preserve(setting.youtube_desc)
                    desc_t = _translate_parts(parts, lang, _translate_text_via_provider)

                if existing:
                    existing.youtube_desc = desc_t
                    existing.source_hash = source_hash_value
                    existing.save(update_fields=['youtube_desc', 'source_hash', 'updated_at'])
                else:
                    SiteSettingTranslation.objects.create(
                        setting=setting,
                        lang=lang,
                        youtube_desc=desc_t,
                        source_hash=source_hash_value,
                    )
                logger.info(f'YouTube desc translation saved for {lang}')
            except Exception:
                logger.exception('YouTube desc translation failed for lang=%s', lang)

        close_old_connections()

    def _start_background():
        t = threading.Thread(
            target=_run_translation,
            args=(instance.pk, source_hash),
            daemon=True,
            name=f"translate-sitesetting-{instance.pk}",
        )
        t.start()

    transaction.on_commit(_start_background)