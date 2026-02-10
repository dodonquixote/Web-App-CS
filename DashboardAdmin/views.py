from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Category, Article
from .forms import ArticleForm
from django.contrib.messages import get_messages
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.text import Truncator
from django.contrib import messages
from django.http import Http404
from django.contrib.messages import get_messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import re
from .forms import SiteSettingForm
from .models import SiteSetting
from django.db.models import Q
from django.utils.html import strip_tags

from django.views.decorators.http import require_POST
from django.http import JsonResponse
import re
try:
    import requests
except Exception:
    requests = None

@login_required
def list_articles(request):
    # List all articles with basic info
    # Consume and clear any pending messages so stale validation errors don't show on list page
    list(get_messages(request))

    qs = Article.objects.all().order_by('-created_at')

    # Apply filters from GET params (status, category, q)
    status = (request.GET.get('status') or '').strip()
    category = (request.GET.get('category') or '').strip()
    q = (request.GET.get('q') or '').strip()

    if status in ('published', 'draft', 'archived'):
        qs = qs.filter(status=status)

    if category:
        # template sends category name; filter by related Category name
        qs = qs.filter(category__name=category)

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    # paginate server-side
    try:
        page = int(request.GET.get('page', '1'))
        if page < 1:
            page = 1
    except Exception:
        page = 1

    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(qs, 10)
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    # also pass categories for filters
    categories = Category.objects.all()
    return render(request, 'dashboard/list_article.html', {'articles': page_obj.object_list, 'categories': categories, 'page_obj': page_obj, 'paginator': paginator})
# Create your views here.
@login_required
def index(request):
    # Show form and list of categories; handle article creation
    # Consume any pending messages so settings-save messages don't appear on Add Article page
    list(get_messages(request))
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.admin = request.user
            # If published and no published_at specified, set now
            if article.status == 'published' and not article.published_at:
                article.published_at = timezone.now()
            article.save()
            messages.success(request, 'Article saved successfully.')
            # clear any prior error messages so they don't show up on the next page
            list(get_messages(request))
            # redirect to articles list with a flag so the list view can render fresh
            return redirect(f"{reverse('DashboardAdmin:list_articles')}?created=1")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ArticleForm()

    categories = Category.objects.all()
    return render(request, 'dashboard/dashboard.html', {'form': form, 'categories': categories})


def login(request):
    # Allow GET to show form and POST to authenticate
    context = {}
    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = None
        # Try authenticate directly with provided username
        if username_or_email:
            user = authenticate(request, username=username_or_email, password=password)

        # If not authenticated, try treating input as email
        if user is None:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.is_active and user.is_superuser:
                auth_login(request, user)
                return redirect('DashboardAdmin:index')
            else:
                context['error'] = 'Only superuser accounts are allowed to log in here.'
        else:
            context['error'] = 'Invalid credentials.'

    return render(request, 'login/login.html', context)


def logout(request):
    auth_logout(request)
    return redirect('DashboardAdmin:login')


@login_required
def view_article(request, slug):
    # Admin view for a single article (lookup by slug)
    article = get_object_or_404(Article, slug=slug)
    return render(request, 'dashboard/article_detail.html', {'article': article})


@login_required
def edit_article(request, slug):
    article = get_object_or_404(Article, slug=slug)
    if request.method == 'POST':
        # Ensure the submitted article_id does not trigger uniqueness validation
        post = request.POST.copy()
        # remove article_id from bound data so the ModelForm won't try to validate/change it
        post.pop('article_id', None)
        form = ArticleForm(post, request.FILES, instance=article)
        # disable article_id on the bound form so it's not validated as missing
        try:
            form.fields['article_id'].disabled = True
        except Exception:
            pass
        if form.is_valid():
            a = form.save(commit=False)
            # keep admin as is
            # handle remove image checkbox
            if request.POST.get('remove_image'):
                a.featured_image = None
            else:
                # if user didn't upload a new file, preserve existing image
                if not request.FILES.get('featured_image'):
                    a.featured_image = article.featured_image
            a.save()
            messages.success(request, 'Article updated successfully.')
            # consume any previous messages (for example prior validation errors)
            list(get_messages(request))
            # After editing, go to the articles list so user sees updated data immediately
            return redirect(f"{reverse('DashboardAdmin:list_articles')}?updated=1")
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ArticleForm(instance=article)
        # When showing the edit form, make article_id read-only/disabled so users don't change it here.
        try:
            form.fields['article_id'].disabled = True
        except Exception:
            pass
        # Ensure category choices are available and published_at is formatted
        try:
            form.fields['category'].queryset = Category.objects.all()
        except Exception:
            pass
        if article.published_at:
            # format for datetime-local input: YYYY-MM-DDTHH:MM
            local_dt = timezone.localtime(article.published_at)
            form.initial['published_at'] = local_dt.strftime('%Y-%m-%dT%H:%M')
    categories = Category.objects.all()
    return render(request, 'dashboard/edit_article.html', {'form': form, 'article': article, 'categories': categories})


@login_required
def delete_article(request, slug):
    try:
        article = Article.objects.get(slug=slug)
    except Article.DoesNotExist:
        # If this was an AJAX/fetch delete request, return JSON instead of raising a 404 page.
        if request.method == 'POST' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Article not found'}, status=404)
        # For normal GET views, raise Http404 so the standard 404 page is shown.
        raise Http404('No Article matches the given query.')

    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Article deleted.')
        # consume any previous messages so list page is clean
        list(get_messages(request))
        # If this is an AJAX delete, return JSON for the frontend to handle
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.META.get('CONTENT_TYPE') == 'application/json':
            return JsonResponse({'success': True})
        return redirect('DashboardAdmin:list_articles')

    return render(request, 'dashboard/confirm_delete.html', {'article': article})



@login_required
@require_POST
def pin_article(request, slug):
    """Toggle or set pin state for an article. Only one article per category will remain pinned.

    POST params:
      - pin: optional, '1' or 'true' to pin, '0' or 'false' to unpin. If omitted, toggles current state.

    Returns JSON: { success: True, pinned: bool }
    """
    article = get_object_or_404(Article, slug=slug)
    val = request.POST.get('pin', None)
    if val is None:
        article.is_pinned = not bool(article.is_pinned)
    else:
        article.is_pinned = True if str(val).lower() in ('1', 'true', 'yes', 'on') else False
    article.save()
    return JsonResponse({'success': True, 'pinned': article.is_pinned})


@login_required
@require_POST
def upload_image(request):
    """Accept an image upload (TinyMCE) and return JSON with `location` key.

    Expects file under form field `file` (TinyMCE default) or `featured_image`.
    Returns: { "location": "/media/.." }
    """
    upload = request.FILES.get('file') or request.FILES.get('featured_image')
    if not upload:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    # Create a safe path under MEDIA_ROOT/articles/
    upload_dir = 'articles'
    filename = upload.name
    # ensure unique filename
    base, ext = os.path.splitext(filename)
    counter = 0
    dest_name = f"{base}{ext}"
    while default_storage.exists(os.path.join(upload_dir, dest_name)):
        counter += 1
        dest_name = f"{base}-{counter}{ext}"

    path = default_storage.save(os.path.join(upload_dir, dest_name), ContentFile(upload.read()))
    try:
        url = default_storage.url(path)
    except Exception:
        # fallback: build from MEDIA_URL
        url = settings.MEDIA_URL.rstrip('/') + '/' + path

    return JsonResponse({'location': url})


@login_required
def settings_view(request):
    setting = SiteSetting.get_solo()
    if request.method == 'POST':
        # If user clicked the per-field save buttons, handle each separately
        if 'save_spotify' in request.POST:
            raw = request.POST.get('spotify_link', '').strip()
            # Extract playlist id from common Spotify URL formats
            # Examples:
            # https://open.spotify.com/playlist/{id}
            # https://open.spotify.com/playlist/{id}?si=...
            # spotify:playlist:{id}
            pid = None
            if raw:
                m = re.search(r'playlist[/:]([A-Za-z0-9]+)', raw)
                if m:
                    pid = m.group(1)
                else:
                    # maybe user pasted only id
                    m2 = re.match(r'^([A-Za-z0-9]+)$', raw)
                    if m2:
                        pid = m2.group(1)
            if pid:
                embed = f'https://open.spotify.com/embed/playlist/{pid}?utm_source=generator&theme=1'
                setting.spotify_link = embed
                setting.save()
                messages.success(request, 'Spotify playlist saved.')
            else:
                messages.error(request, 'Could not extract Spotify playlist ID. Please paste full playlist URL or ID.')
            return redirect('DashboardAdmin:settings')

        if 'save_youtube' in request.POST:
            # Normalize YouTube input into embed URL. Accept watch?v=..., youtu.be/..., /embed/..., or raw ID
            raw = request.POST.get('youtube_link', '').strip()
            vid = None
            if raw:
                m = re.search(r'(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{6,})', raw)
                if m:
                    vid = m.group(1)
                else:
                    m2 = re.match(r'^([A-Za-z0-9_-]{6,})$', raw)
                    if m2:
                        vid = m2.group(1)
            if vid:
                # quick oEmbed check to ensure video allows embedding
                oembed_ok = True
                if requests is None:
                    # cannot verify on server; warn but save normalized embed
                    messages.warning(request, 'requests library not available on server to verify embeddability. Saved anyway.')
                else:
                    try:
                        oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
                        resp = requests.get(oembed_url, timeout=6)
                        if resp.status_code != 200:
                            oembed_ok = False
                    except Exception:
                        oembed_ok = False

                if not oembed_ok:
                    messages.error(request, 'YouTube video does not appear embeddable (owner may have disabled embedding or it is restricted). The link was not saved.');
                else:
                    embed = f'https://www.youtube.com/embed/{vid}'
                    setting.youtube_link = embed
                    setting.save()
                    messages.success(request, 'YouTube link saved.')
            else:
                messages.error(request, 'Could not extract YouTube video ID. Please paste a full YouTube URL or the video ID.')
            return redirect('DashboardAdmin:settings')

        if 'save_youtube_desc' in request.POST:
            # Save the HTML formatted description from TinyMCE, converting it back to plain text with newlines
            raw_desc = request.POST.get('youtube_desc', '')
            
            # Convert HTML back to plain text while preserving paragraph breaks
            # <p>text</p> and <br> become newlines
            plain_text = raw_desc
            plain_text = re.sub(r'</p>\s*<p>', '\n\n', plain_text)  # Between paragraphs: double newline
            plain_text = re.sub(r'<p>(.*?)</p>', r'\1', plain_text, flags=re.DOTALL)  # Remove <p> tags
            plain_text = re.sub(r'<br\s*/?>', '\n', plain_text, flags=re.IGNORECASE)  # <br> to newline
            plain_text = re.sub(r'<[^>]+>', '', plain_text)  # Remove any remaining tags
            plain_text = plain_text.strip()
            
            setting.youtube_desc = plain_text
            setting.save()
            messages.success(request, 'YouTube description saved.')
            return redirect('DashboardAdmin:settings')

        if 'save_translate' in request.POST:
            # Save translate API settings
            url = request.POST.get('translate_api_url', '').strip()
            key = request.POST.get('translate_api_key', '').strip()
            setting.translate_api_url = url
            setting.translate_api_key = key
            setting.save()
            messages.success(request, 'Translate settings saved.')
            return redirect('DashboardAdmin:settings')

        if 'remove_ad_left' in request.POST:
            setting.ad_left = None
            setting.save()
            messages.success(request, 'Left ad removed.')
            return redirect('DashboardAdmin:settings')

        if 'remove_ad_right' in request.POST:
            setting.ad_right = None
            setting.save()
            messages.success(request, 'Right ad removed.')
            return redirect('DashboardAdmin:settings')

        if 'remove_ad_top' in request.POST:
            setting.ad_top = None
            setting.save()
            messages.success(request, 'Top ad removed.')
            return redirect('DashboardAdmin:settings')

        if 'remove_ad_down' in request.POST:
            setting.ad_down = None
            setting.save()
            messages.success(request, 'Bottom ad removed.')
            return redirect('DashboardAdmin:settings')

        if 'save_ads' in request.POST:
            # handle uploaded ad images
            # left
            if request.FILES.get('ad_left'):
                setting.ad_left = request.FILES.get('ad_left')
            # left link
            try:
                setting.ad_left_link = (request.POST.get('ad_left_link') or '').strip()
            except Exception:
                pass
            # right
            if request.FILES.get('ad_right'):
                setting.ad_right = request.FILES.get('ad_right')
            # right link
            try:
                setting.ad_right_link = (request.POST.get('ad_right_link') or '').strip()
            except Exception:
                pass
            # down
            if request.FILES.get('ad_down'):
                setting.ad_down = request.FILES.get('ad_down')
            # down link
            try:
                setting.ad_down_link = (request.POST.get('ad_down_link') or '').strip()
            except Exception:
                pass

            # top (new fourth ad)
            if request.FILES.get('ad_top'):
                setting.ad_top = request.FILES.get('ad_top')
            # top link
            try:
                setting.ad_top_link = (request.POST.get('ad_top_link') or '').strip()
            except Exception:
                pass

            setting.save()
            messages.success(request, 'Ad images updated.')
            return redirect('DashboardAdmin:settings')

        # Fallback: full form submit (legacy)
        form = SiteSettingForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            # Ensure any provided YouTube value is normalized to embed URL before saving
            raw_y = request.POST.get('youtube_link', '').strip()
            vid = None
            if raw_y:
                m = re.search(r'(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{6,})', raw_y)
                if m:
                    vid = m.group(1)
                else:
                    m2 = re.match(r'^([A-Za-z0-9_-]{6,})$', raw_y)
                    if m2:
                        vid = m2.group(1)

            if vid:
                # verify embeddability via oEmbed before saving
                oembed_ok = True
                if requests is None:
                    messages.warning(request, 'requests library not available; cannot verify YouTube embeddability. Saving value.')
                else:
                    try:
                        oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
                        resp = requests.get(oembed_url, timeout=6)
                        if resp.status_code != 200:
                            oembed_ok = False
                    except Exception:
                        oembed_ok = False

                if not oembed_ok:
                    messages.error(request, 'Provided YouTube video does not appear embeddable (owner may have disabled embedding or it is restricted). Please provide a different video or leave the field blank.')
                    return redirect('DashboardAdmin:settings')
                form.instance.youtube_link = f'https://www.youtube.com/embed/{vid}'

            # If youtube_desc provided on full-form submit, convert HTML formatting to plain text with newlines
            raw_desc = request.POST.get('youtube_desc', None)
            if raw_desc is not None:
                # Convert HTML back to plain text while preserving paragraph breaks
                plain_text = raw_desc
                plain_text = re.sub(r'</p>\s*<p>', '\n\n', plain_text)  # Between paragraphs: double newline
                plain_text = re.sub(r'<p>(.*?)</p>', r'\1', plain_text, flags=re.DOTALL)  # Remove <p> tags
                plain_text = re.sub(r'<br\s*/?>', '\n', plain_text, flags=re.IGNORECASE)  # <br> to newline
                plain_text = re.sub(r'<[^>]+>', '', plain_text)  # Remove any remaining tags
                form.instance.youtube_desc = plain_text.strip()

            form.save()
            messages.success(request, 'Site settings updated.')
            return redirect('DashboardAdmin:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SiteSettingForm(instance=setting)

    return render(request, 'dashboard/settings.html', {'form': form})


@login_required
@require_POST
def fetch_youtube_desc(request):
    if requests is None:
        return JsonResponse({'success': False, 'error': 'requests library not available'}, status=500)

    setting = SiteSetting.get_solo()
    raw = request.POST.get('youtube_link', '').strip() or setting.youtube_link or ''

    # extract video id
    vid = None
    m = re.search(r'(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{6,})', raw)
    if m:
        vid = m.group(1)
    elif re.match(r'^[A-Za-z0-9_-]{6,}$', raw):
        vid = raw

    if not vid:
        return JsonResponse({'success': False, 'error': 'Invalid YouTube video id'}, status=400)

    # IMPORTANT: use mobile site
    url = f'https://m.youtube.com/watch?v={vid}'

    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10)'
            }
        )
        html = resp.text
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # === CORE FIX: get meta description directly ===
    desc = None
    matches = re.findall(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        html,
        flags=re.IGNORECASE | re.DOTALL
    )

    desc = None
    if matches:
        # ambil description TERPANJANG
        desc = max(matches, key=lambda x: len(x.strip()))


    if not desc:
        return JsonResponse({'success': False, 'error': 'Description meta not found'}, status=404)

    # cleanup & normalize
    try:
        import html as _html
        desc = _html.unescape(desc)
    except Exception:
        pass

    # Normalize newlines and whitespace
    desc = desc.replace('\r\n', '\n').replace('\r', '\n')
    desc = desc.replace('\u00a0', ' ')  # non-breaking space to regular space
    
    # Clean up excessive whitespace: collapse multiple newlines to max 2 (for paragraph breaks)
    desc = re.sub(r'\n\s*\n+', '\n\n', desc)  # Multiple newlines → double newline
    desc = re.sub(r'[ \t]+', ' ', desc)  # Multiple spaces/tabs → single space
    desc = desc.strip()  # Trim leading/trailing whitespace

    # Return both plain text and an optional HTML version with linkified URLs.
    def linkify(text):
        return re.sub(
            r'(https?://[^\s<]+)',
            r'<a href="\1" target="_blank" rel="noopener noreferrer" style="font-weight: bold; color: #2563eb; text-decoration: underline;">\1</a>',
            text
        )

    plain_desc = desc
    html_desc = linkify(plain_desc)

    return JsonResponse({
        'success': True,
        'desc': plain_desc,
        'desc_html': html_desc
    })



@login_required
def debug_settings(request):
    """Admin-only debug endpoint returning current SiteSetting ad fields and file existence."""
    setting = SiteSetting.get_solo()
    data = {
        'spotify_link': setting.spotify_link,
        'youtube_link': setting.youtube_link,
        'youtube_desc': setting.youtube_desc,
        'ad_left': None,
        'ad_right': None,
        'ad_down': None,
        'ad_top': None,
    }
    try:
        if setting.ad_left and getattr(setting.ad_left, 'url', None):
            data['ad_left'] = setting.ad_left.url
            data['ad_left_exists'] = default_storage.exists(setting.ad_left.name)
        else:
            data['ad_left_exists'] = False
    except Exception:
        data['ad_left_exists'] = False
    try:
        if setting.ad_right and getattr(setting.ad_right, 'url', None):
            data['ad_right'] = setting.ad_right.url
            data['ad_right_exists'] = default_storage.exists(setting.ad_right.name)
        else:
            data['ad_right_exists'] = False
    except Exception:
        data['ad_right_exists'] = False
    try:
        if setting.ad_down and getattr(setting.ad_down, 'url', None):
            data['ad_down'] = setting.ad_down.url
            data['ad_down_exists'] = default_storage.exists(setting.ad_down.name)
        else:
            data['ad_down_exists'] = False
    except Exception:
        data['ad_down_exists'] = False
    try:
        if setting.ad_top and getattr(setting.ad_top, 'url', None):
            data['ad_top'] = setting.ad_top.url
            data['ad_top_exists'] = default_storage.exists(setting.ad_top.name)
        else:
            data['ad_top_exists'] = False
    except Exception:
        data['ad_top_exists'] = False

    return JsonResponse({'success': True, 'setting': data})

