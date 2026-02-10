// Simple client-side i18n
const TRANSLATIONS = {
    id: {
        'nav.home': 'Beranda',
        'nav.anime': 'Anime',
        'nav.game': 'Game',
        'nav.geek': 'Geek',
        'nav.event': 'Event',
        'index.latest_anime': 'Latest Anime Update',
        'index.latest_game': 'Latest Game Update',
        'index.latest_geek': 'Latest Geek Update',
        'btn.read_more': 'Baca lebih lanjut',
        'btn.back_to_top': 'Back To Top',
        'index.top_music': 'Top Music of The Month',
        'index.spotify_desc': 'Playlist resmi komunitas CleanSound di Spotify',
        'index.spotify_link': 'Lihat playlist lengkap di Spotify',
        'index.vote_question': 'Ingin lagu favoritmu masuk ke chart bulan depan?',
        'index.vote_link': 'Ikut voting Top Music di sini!',
        'index.latest_video': 'Video Terbaru',
        'no.articles': 'Tidak ada artikel untuk ditampilkan.',
        'no.anime': 'Belum ada artikel anime.',
        'no.game': 'Belum ada artikel game.',
        'no.geek': 'Belum ada artikel geek.',
        'article.you_may_like': 'Anda mungkin juga menyukai',
        'article.discover_more': 'Temukan lebih banyak'
        ,
        // Category Pages
        'category.anime': 'Kategori Anime!',
        'category.game': 'Kategori Game!',
        'category.geek': 'Kategori Geek!',
        'category.event': 'Kategori Event!'
        ,
        // Navbar / Footer / UI
        'nav.logo_tag': 'CLEANSOUND',
        'btn.watch_on_youtube': 'Tonton di YouTube',
        'section.top_music': 'Top Music of The Month',
        'footer.social': 'Media Sosial Kami',
        'footer.tagline': 'Stay Clean & Sound',
        'footer.email': 'cleansoundstudio@gmail.com',
        'footer.copy': '© 2025 CLEANSOUND Portal Berita. Hak cipta dilindungi.',
        'mobile.menu': 'MENU',
        'mobile.category': 'Kategori',
        'mobile.translation': 'Terjemahan',
        'lang.indonesia': 'Indonesia',
        'lang.english': 'English',
        'lang.japanese': 'Japanese'
    },
    en: {
        'nav.home': 'Home',
        'nav.anime': 'Anime',
        'nav.game': 'Game',
        'nav.geek': 'Geek',
        'nav.event': 'Event',
        'index.latest_anime': 'Latest Anime Update',
        'index.latest_game': 'Latest Game Update',
        'index.latest_geek': 'Latest Geek Update',
        'btn.read_more': 'Read more',
        'btn.back_to_top': 'Back To Top',
        'index.top_music': 'Top Music of The Month',
        'index.spotify_desc': 'Official CleanSound community playlist on Spotify',
        'index.spotify_link': 'See full playlist on Spotify',
        'index.vote_question': 'Want your favorite song in next month\'s chart?',
        'index.vote_link': 'Vote for Top Music here!',
        'index.latest_video': 'Latest Video',
        'no.articles': 'No articles to display.',
        'no.anime': 'No anime articles yet.',
        'no.game': 'No game articles yet.',
        'no.geek': 'No geek articles yet.',
        'article.you_may_like': 'You may also like',
        'article.discover_more': 'Discover more'
        ,
        // Category Pages
        'category.anime': 'Category Anime!',
        'category.game': 'Category Game!',
        'category.geek': 'Category Geek!',
        'category.event': 'Category Event!'
        ,
        // Navbar / Footer / UI
        'nav.logo_tag': 'CLEANSOUND',
        'btn.watch_on_youtube': 'Watch on YouTube',
        'section.top_music': 'Top Music of The Month',
        'footer.social': 'Our Social Media',
        'footer.tagline': 'Stay Clean & Sound',
        'footer.email': 'cleansoundstudio@gmail.com',
        'footer.copy': '© 2025 CLEANSOUND News Portal. All rights reserved.',
        'mobile.menu': 'MENU',
        'mobile.category': 'Category',
        'mobile.translation': 'Translation',
        'lang.indonesia': 'Indonesia',
        'lang.english': 'English',
        'lang.japanese': 'Japanese'
    },
    ja: {
        'nav.home': 'ホーム',
        'nav.anime': 'アニメ',
        'nav.game': 'ゲーム',
        'nav.geek': 'ギーク',
        'nav.event': 'イベント',
        'index.latest_anime': '最新のアニメ',
        'index.latest_game': '最新のゲーム',
        'index.latest_geek': '最新のギーク',
        'btn.read_more': '続きを読む',
        'btn.back_to_top': 'トップへ戻る',
        'index.top_music': '今月のトップミュージック',
        'index.spotify_desc': 'SpotifyのCleanSoundコミュニティ公式プレイリスト',
        'index.spotify_link': 'Spotifyで完全なプレイリストを見る',
        'index.vote_question': '来月のチャートにお気に入りの曲を入れたいですか？',
        'index.vote_link': 'こちらでトップミュージックに投票！',
        'index.latest_video': '最新動画',
        'no.articles': '表示する記事がありません。',
        'no.anime': 'アニメの記事はまだありません。',
        'no.game': 'ゲームの記事はまだありません。',
        'no.geek': 'ギークの記事はまだありません。',
        'article.you_may_like': 'あなたにおすすめ',
        'article.discover_more': 'もっと見る'
        ,
        // Category Pages
        'category.anime': 'アニメカテゴリー！',
        'category.game': 'ゲームカテゴリー！',
        'category.geek': 'ギークカテゴリー！',
        'category.event': 'イベントカテゴリー！'
        ,
        // Navbar / Footer / UI
        'nav.logo_tag': 'CLEANSOUND',
        'btn.watch_on_youtube': 'YouTubeで見る',
        'section.top_music': '今月のトップ音楽',
        'footer.social': 'ソーシャルメディア',
        'footer.tagline': 'Stay Clean & Sound',
        'footer.email': 'cleansoundstudio@gmail.com',
        'footer.copy': '© 2025 CLEANSOUND ニュースポータル。全著作権所有。',
        'mobile.menu': 'メニュー',
        'mobile.category': 'カテゴリー',
        'mobile.translation': '翻訳',
        'lang.indonesia': 'インドネシア語',
        'lang.english': '英語',
        'lang.japanese': '日本語'
    }
};

function getStoredLang() {
    // PRIORITY 1: Detect from URL path
    const path = window.location.pathname;
    const pathMatch = path.match(/^(\/(en|jp|ja|id))?/);
    if (pathMatch && pathMatch[2]) {
        const urlLang = pathMatch[2];
        // Normalize jp to ja
        return urlLang === 'jp' ? 'ja' : urlLang;
    }
    
    // PRIORITY 2: Fallback to localStorage
    const stored = localStorage.getItem('lang');
    if (stored) {
        return stored === 'jp' ? 'ja' : stored;
    }
    
    // PRIORITY 3: Default Indonesian
    return 'id';
}

function setStoredLang(lang) {
    localStorage.setItem('lang', lang);
}

export function translatePage(lang) {
    const map = TRANSLATIONS[lang] || TRANSLATIONS['id'];
    
    // Get all article.non-prose elements to exclude from translation
    const articleElements = document.querySelectorAll('article.non-prose');
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (!key) return;
        
        // Skip translation if element has data-no-translate attribute
        if (el.hasAttribute('data-no-translate')) return;
        
        // Skip translation if element is inside ANY article.non-prose
        let isInsideArticle = false;
        articleElements.forEach(articleEl => {
            if (articleEl.contains(el)) {
                isInsideArticle = true;
            }
        });
        if (isInsideArticle) return;
        
        // Skip translation if element is an iframe with YouTube src
        if (el.tagName === 'IFRAME' && el.src && el.src.includes('youtube')) return;
        
        // Skip translation if element is an anchor with YouTube href
        if (el.tagName === 'A' && el.href && el.href.includes('youtube')) return;
        
        const txt = map[key];
        if (txt !== undefined) {
            // If element is input/placeholder, set placeholder
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = txt;
            } else {
                el.textContent = txt;
            }
        }
    });
}

function bindLangButtons() {
    // Buttons with data-lang attribute will navigate to language URL
    document.querySelectorAll('[data-lang]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const lang = btn.dataset.lang;
            if (!lang) return;
            
            // Navigate to the URL with language prefix
            const path = window.location.pathname;
            const search = window.location.search;
            const hash = window.location.hash;
            
            let newPath = path;
            
            // Remove existing language prefix if present
            // Current path could be: /, /en/, /jp/, /ja/, /id/, /article/slug/, /en/article/slug/, etc.
            const pathMatch = path.match(/^(\/(en|jp|ja|id))?(.*)$/);
            const basePath = pathMatch ? pathMatch[3] || '/' : path;
            
            // Add new language prefix
            if (lang === 'id') {
                // Indonesian has no prefix
                newPath = basePath;
            } else if (lang === 'jp') {
                // Normalize jp to ja
                newPath = `/ja${basePath}`;
            } else {
                // English and Japanese have prefixes
                newPath = `/${lang}${basePath}`;
            }
            
            // Navigate to new language URL
            window.location.href = newPath + search + hash;
        });
    });
}

export function initI18n() {
    // Call after DOM (and navbar) is loaded
    const lang = getStoredLang();
    translatePage(lang);
    bindLangButtons();
    
    // Watch for dynamically added elements with data-i18n
    // This observer will retranslate when new content is added to the page
    const observer = new MutationObserver((mutations) => {
        // Check if any new elements with data-i18n were added
        const hasNewI18n = mutations.some(m => {
            return Array.from(m.addedNodes).some(node => {
                if (node.nodeType === 1) { // Element node
                    return node.hasAttribute && (node.hasAttribute('data-i18n') || node.querySelector('[data-i18n]'));
                }
                return false;
            });
        });
        
        if (hasNewI18n) {
            // Retranslate the entire page with current language
            translatePage(getCurrentLang());
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

export function getCurrentLang() { return getStoredLang(); }
