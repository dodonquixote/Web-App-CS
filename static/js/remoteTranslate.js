// Client-side translation loader: fetches pre-translated articles only.

async function postJson(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!res.ok) {
        let msg = `HTTP ${res.status}`;
        try {
            const j = await res.json();
            if (j && j.error) msg += `: ${j.error}`;
            if (j && j.details) msg += ` - ${j.details}`;
        } catch (_) {
            const text = await res.text();
            if (text) msg += `: ${text}`;
        }
        throw new Error(msg);
    }
    return res.json();
}

function showLoading() {
    let el = document.getElementById('remote-translate-loading');
    if (!el) {
        el = document.createElement('div');
        el.id = 'remote-translate-loading';
        el.style.position = 'fixed';
        el.style.right = '12px';
        el.style.bottom = '12px';
        el.style.zIndex = 99999;
        el.style.padding = '8px 12px';
        el.style.background = 'rgba(0,0,0,0.7)';
        el.style.color = 'white';
        el.style.borderRadius = '8px';
        el.style.fontSize = '13px';
        el.textContent = 'Loading translation...';
        document.body.appendChild(el);
    }
}

function hideLoading() {
    const el = document.getElementById('remote-translate-loading');
    if (el) el.remove();
}

function convertYouTubeURLsToEmbeds(container) {
    try {
        // Convert plain YouTube URLs to iframe embeds (like autoembed filter)
        const youtubePattern = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([A-Za-z0-9_-]{6,})(?:[^\s<>"]*)?/gi;
        
        function walkTextNodes(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                const text = node.textContent;
                if (youtubePattern.test(text)) {
                    const fragment = document.createDocumentFragment();
                    let lastIndex = 0;
                    youtubePattern.lastIndex = 0;
                    let match;
                    
                    while ((match = youtubePattern.exec(text)) !== null) {
                        // Add text before match
                        if (match.index > lastIndex) {
                            fragment.appendChild(document.createTextNode(text.substring(lastIndex, match.index)));
                        }
                        
                        // Create iframe embed
                        const vid = match[1];
                        const wrapper = document.createElement('div');
                        wrapper.className = 'w-full aspect-video mb-6';
                        const iframe = document.createElement('iframe');
                        iframe.src = `https://www.youtube.com/embed/${vid}`;
                        iframe.setAttribute('frameborder', '0');
                        iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
                        iframe.setAttribute('allowfullscreen', '');
                        wrapper.appendChild(iframe);
                        fragment.appendChild(wrapper);
                        
                        lastIndex = match.index + match[0].length;
                    }
                    
                    // Add remaining text
                    if (lastIndex < text.length) {
                        fragment.appendChild(document.createTextNode(text.substring(lastIndex)));
                    }
                    
                    if (lastIndex > 0) {
                        node.parentNode.replaceChild(fragment, node);
                    }
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                // Skip existing iframes and script tags
                if (node.tagName !== 'IFRAME' && node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
                    Array.from(node.childNodes).forEach(child => walkTextNodes(child));
                }
            }
        }
        
        walkTextNodes(container);
    } catch (err) {
        console.warn('convertYouTubeURLsToEmbeds error:', err);
    }
}

function unwrapIframeLinks() {
    try {
        const anchors = document.querySelectorAll('article.non-prose a');
        anchors.forEach(a => {
            const iframe = a.querySelector('iframe');
            if (!iframe) return;

            const wrapper = iframe.closest('div') || iframe;
            a.parentNode.insertBefore(wrapper, a);
            a.remove();
        });
    } catch (err) {
        console.warn('unwrapIframeLinks error:', err);
    }
}

function reinitYouTubeIframes() {
    try {
        unwrapIframeLinks();
        const iframes = document.querySelectorAll('article.non-prose iframe[src*="youtube.com/embed/"], article.non-prose iframe[src*="youtube-nocookie.com/embed/"]');
        iframes.forEach(iframe => {
            try {
                const src = iframe.getAttribute('src') || '';
                const url = new URL(src, location.href);
                url.searchParams.set('enablejsapi', '1');
                url.searchParams.set('rel', '0');
                url.searchParams.set('modestbranding', '1');
                url.searchParams.set('origin', location.origin);
                iframe.src = url.toString();
                iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
                iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
            } catch (e) {
                console.warn('Failed to reinit iframe:', e);
            }
        });
    } catch (err) {
        console.warn('reinitYouTubeIframes error:', err);
    }
}

export async function translateCurrentPage(lang) {
    try {
        showLoading();
        const segments = window.location.pathname.split('/').filter(s => s.length > 0);
        if (segments.length >= 2 && segments[0] === 'article') {
            const slug = segments[1];
            const payload = { page: 'article', slug, lang };
            const data = await postJson('/api/translate/', payload);

            if (data.title) {
                const titleEl = document.getElementById('article-title');
                if (titleEl) titleEl.textContent = data.title;
                document.title = data.title + ' - CLEANSOUND';
            }

            if (data.content) {
                const articleEl = document.querySelector('article.non-prose');
                if (articleEl) {
                    articleEl.innerHTML = data.content;
                    if (typeof window.initArticleYouTubeEmbeds === 'function') {
                        window.initArticleYouTubeEmbeds();
                    }
                }
            }
        }
        hideLoading();
    } catch (err) {
        hideLoading();
        console.error('Remote translation failed:', err);
        const el = document.createElement('div');
        el.style.position = 'fixed';
        el.style.right = '12px';
        el.style.bottom = '12px';
        el.style.zIndex = 99999;
        el.style.padding = '8px 12px';
        el.style.background = 'rgba(200,40,40,0.95)';
        el.style.color = 'white';
        el.style.borderRadius = '8px';
        el.style.fontSize = '13px';
        el.textContent = 'Translation failed: ' + (err && err.message ? err.message : 'unknown error');
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 4000);
    }
}

window.addEventListener('languageChanged', (e) => {
    const lang = e?.detail?.lang;
    if (!lang) return;
    translateCurrentPage(lang).catch(err => console.error(err));
});

// Export function to window for use in article.html
window.convertYouTubeURLsToEmbeds = convertYouTubeURLsToEmbeds;

window.addEventListener('DOMContentLoaded', () => {
    console.log('[remoteTranslate] DOMContentLoaded - using simple YouTube iframes from autoembed');
    // Don't call initArticleYouTubeEmbeds or convert URLs
    // The autoembed filter already created proper iframes in the template
    // Just let them load naturally without any Player API interference
});

export default { translateCurrentPage };
