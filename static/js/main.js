// 1. IMPORT COMPONENT
import { Hero } from './components/Hero.js';
import { SubHero } from './components/SubHero.js';
import { CardGrid } from './components/CardGrid.js';
import { CardHome } from './components/CardHome.js';
import { initLayout } from './utils/layout.js';
import { initI18n, translatePage, getCurrentLang } from './i18n.js';
// remoteTranslate listens to languageChanged events and calls the backend translate API
import './remoteTranslate.js';

// =========================================
// 0. CONFIG & STATE
// =========================================
const ITEMS_PAGE_1 = 11;      
const ITEMS_OTHER_PAGES = 12; 
let currentPage = 1;
let currentData = [];
let currentTotalPages = 1;
// [NEW] KONFIGURASI SLIDER HERO (FUTURE PROOF)
// Nanti Admin Dashboard tinggal update array ini untuk mengubah isi slider
const HERO_CONFIG = [
    { type: 'category', source: 'event.html', index: 0 }, // Slide 1: Ambil Event Terbaru
    { type: 'category', source: 'anime.html', index: 0 }, // Slide 2: Ambil Anime Terbaru
    { type: 'category', source: 'game.html',  index: 0 }, // Slide 3: Ambil Game Terbaru (BARU)
    { type: 'category', source: 'geek.html',  index: 0 }, // Slide 4: Ambil Geek Terbaru
    // { type: 'manual', title: "Special Promo!", category: "Promo", img: "/static/public/images/SLD1.png", desc: "Don't miss our special promo!" }
    // Contoh jika Admin mau PIN berita spesifik (Manual):
    // { type: 'manual', id: 999, title: "Promo Spesial", category: "Promo", img: "/static/public/images/promo.png", desc: "Diskon merdeka!" }
];

// Map UI path slug -> backend category name when they differ
const SLUG_TO_CATEGORY = {
    game: 'gaming',
    gaming: 'gaming',
    anime: 'anime',
    geek: 'geek',
    event: 'event'
};


// =========================================
// 2. LOGIKA HOMEPAGE (Slider & Grid Berita)
// =========================================
// Render Slide Hero Dinamis & Bisa Custom
function renderHeroSlides() {
    const sliderContainer = document.getElementById('hero-slider');
    if (!sliderContainer) return;

    console.log("Rendering Hero Slides (No-Crop Mode)...");

    // 1. KUMPULKAN DATA
    let slidesData = [];
    let hasPinnedArticles = false;
    
    // Cek semua kategori yang memiliki artikel pinned
    const categories = {
        'anime': 'anime.html',
        'gaming': 'game.html',
        'geek': 'geek.html',
        'event': 'event.html'
    };
    
    const pinnedSources = [];
    
    for (const [catName, dbKey] of Object.entries(categories)) {
        if (DATABASE[dbKey] && DATABASE[dbKey].length > 0) {
            const firstItem = DATABASE[dbKey][0];
            // Cek apakah artikel pertama adalah pinned (API sudah mengurutkan berdasarkan is_pinned)
            if (firstItem.is_pinned) {
                pinnedSources.push(dbKey);
                hasPinnedArticles = true;
                console.log(`[renderHeroSlides] Found pinned article in ${catName}:`, firstItem.title);
            }
        }
    }
    
    // Jika ada artikel pinned, urutkan ulang HERO_CONFIG
    let orderedConfig = [...HERO_CONFIG];
    if (hasPinnedArticles && pinnedSources.length > 0) {
        // Filter dan reorder: semua kategori pinned dulu, baru yang tidak pinned
        orderedConfig = [
            ...HERO_CONFIG.filter(c => pinnedSources.includes(c.source)),
            ...HERO_CONFIG.filter(c => !pinnedSources.includes(c.source))
        ];
        
        console.log(`[renderHeroSlides] Reordered slides with pinned categories first: ${pinnedSources.join(', ')}`);
    }
    
    orderedConfig.forEach(config => {
        if (config.type === 'category') {
            if (DATABASE[config.source] && DATABASE[config.source][config.index]) {
                slidesData.push(DATABASE[config.source][config.index]);
            }
        } else if (config.type === 'manual') {
            slidesData.push(config);
        }
    });

    if (slidesData.length === 0) return;
    
    // Store pinned status in slider container for use in initHeroSlider
    sliderContainer.dataset.hasPinned = hasPinnedArticles ? 'true' : 'false';

    // 2. GENERATE HTML SLIDES
    let slidesHTML = '';
    
    slidesData.forEach((item, index) => {
        const imgPath = item.img.replace('../../', '/');
        const opacity = index === 0 ? '1' : '0';
        // include data-url so slide can be clickable to open the article
        const slideUrl = item.url || (item.slug ? `/article/${item.slug}/` : '#');
        slidesHTML += `
        <div class="slide absolute inset-0 opacity-0 transition-opacity duration-700 bg-black cursor-pointer" data-url="${slideUrl}" style="opacity: ${opacity}">
            
            <div class="relative w-full h-full overflow-hidden">
                


                <img src="${imgPath}" class="relative z-10 w-full h-full object-cover shadow-lg">
                
                <div class="absolute bottom-4 left-6 bg-black/60 backdrop-blur-sm p-5 rounded-xl w-[85%] md:w-[65%] max-w-md z-20 border border-white/10">
                    <span class="absolute -top-4 left-4 bg-yellow-400 text-black text-xs font-bold px-3 py-1 rounded-full shadow-md">
                        ${item.category}
                    </span>
                    <h2 class="text-white text-md md:text-xl font-extrabold leading-tight mt-1 line-clamp-2">
                        ${item.title}
                    </h2>
                    <p class="text-white text-xs md:text-sm opacity-90 mt-2 line-clamp-2">
                        ${item.desc}
                    </p>
                </div>

            </div>
        </div>`;
    });

    // 3. GENERATE INDICATORS
    let indicatorsHTML = `<div id="hero-indicators" class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 z-30">`;
    slidesData.forEach((_, index) => {
        const opacity = index === 0 ? 'opacity-100' : 'opacity-40';
        indicatorsHTML += `<div class="indicator w-3 h-3 bg-[#EFED3C] rounded-full ${opacity} cursor-pointer transition-all hover:scale-125 shadow-sm border border-black/20"></div>`;
    });
    indicatorsHTML += `</div>`;

    // 4. INSERT
    sliderContainer.innerHTML = slidesHTML + indicatorsHTML;
}

function initHeroSlider() {
    const slider = document.getElementById("hero-slider");
    if (!slider) return; 

    const slides = slider.querySelectorAll(".slide");
    const indicators = document.querySelectorAll("#hero-indicators .indicator");
    if (slides.length === 0) return;

    let index = 0;
    let timer;
    let startX = 0;
    
    // Cek apakah ada artikel yang dipinned
    const hasPinned = slider.dataset.hasPinned === 'true';
    const autoSlideEnabled = !hasPinned; // Matikan auto-slide jika ada artikel pinned
    
    console.log(`[initHeroSlider] Auto-slide ${autoSlideEnabled ? 'enabled' : 'disabled (pinned article detected)'}`);

    function showSlide(i) {
        if (i >= slides.length) index = 0;
        else if (i < 0) index = slides.length - 1;
        else index = i;

        slides.forEach((s, idx) => s.style.opacity = idx === index ? "1" : "0");
        if (indicators.length > 0) {
            indicators.forEach((dot, idx) => {
                dot.classList.toggle("opacity-100", idx === index);
                dot.classList.toggle("opacity-40", idx !== index);
            });
        }
    }

    function nextSlide() { showSlide(index + 1); }
    
    indicators.forEach((dot, i) => {
        dot.addEventListener("click", () => {
            if (autoSlideEnabled) {
                clearInterval(timer);
            }
            showSlide(i);
            if (autoSlideEnabled) {
                timer = setInterval(nextSlide, 5000);
            }
        });
    });

    // Make slides clickable: navigate to their `data-url` when clicked/tapped
    slides.forEach(s => {
        s.addEventListener('click', (e) => {
            // avoid clicks on indicator dots triggering navigation
            const url = s.dataset.url;
            if (url && url !== '#') {
                // Allow middle-click / ctrl-click to open in new tab
                if (e.ctrlKey || e.metaKey) {
                    window.open(url, '_blank');
                } else {
                    window.location.href = url;
                }
            }
        });
    });

    // Hanya setup auto-slide jika tidak ada artikel pinned
    if (autoSlideEnabled) {
        slider.addEventListener("mouseenter", () => clearInterval(timer));
        slider.addEventListener("mouseleave", () => timer = setInterval(nextSlide, 5000));
    }
    
    // Touch/swipe tetap berfungsi untuk manual navigation
    slider.addEventListener("touchstart", e => startX = e.touches[0].clientX);
    slider.addEventListener("touchend", e => {
        if (Math.abs(startX - e.changedTouches[0].clientX) > 40) {
            startX - e.changedTouches[0].clientX > 0 ? nextSlide() : showSlide(index - 1);
        }
    });

    showSlide(0);
    
    // Hanya start timer jika auto-slide enabled
    if (autoSlideEnabled) {
        timer = setInterval(nextSlide, 5000);
    }
}
// Render Grid Berita di Homepage (index.html)
function initHomepage() {
    const animeGrid = document.getElementById('home-anime-grid');
    const gameGrid = document.getElementById('home-game-grid');
    const geekGrid = document.getElementById('home-geek-grid');

    if (!animeGrid) return; // Bukan di homepage

    // Render ANIME (Ambil 3 data pertama dari DATABASE)
    const animeData = DATABASE["anime.html"] || [];
    if (animeGrid && animeData.length > 0) {
        // Ubah path gambar agar sesuai dengan index.html (root folder)
        // Replace ../../public menjadi /public
        const fixedData = animeData.slice(0, 3).map(d => ({...d, img: d.img.replace('../../', '/')}));
            // Use CardHome for anime to match Game default appearance
            animeGrid.innerHTML = fixedData.map(item => CardHome(item)).join('');
    }
    else if (animeGrid) {
        animeGrid.innerHTML = `<div class="text-gray-500 italic" data-i18n="no.anime"></div>`;
        translatePage(getCurrentLang());
    }

    // Render GAME
    const gameData = DATABASE["game.html"] || [];
    if (gameGrid && gameData.length > 0) {
        const fixedData = gameData.slice(0, 3).map(d => ({...d, img: d.img.replace('../../', '/')}));
        gameGrid.innerHTML = fixedData.map(item => CardHome(item)).join('');
    }
    else if (gameGrid) {
        gameGrid.innerHTML = `<div class="text-gray-500 italic" data-i18n="no.game"></div>`;
        translatePage(getCurrentLang());
    }

    // Render GEEK
    const geekData = DATABASE["geek.html"] || [];
    if (geekGrid && geekData.length > 0) {
        const fixedData = geekData.slice(0, 3).map(d => ({...d, img: d.img.replace('../../', '/')}));
        geekGrid.innerHTML = fixedData.map(item => CardHome(item)).join('');
    }
    else if (geekGrid) {
        geekGrid.innerHTML = `<div class="text-gray-500 italic" data-i18n="no.geek"></div>`;
        translatePage(getCurrentLang());
    }
}

// =========================================
// 3. DATABASE CENTER
// =========================================
// NOTE: Dummy data removed — frontend will load real data from backend API.
const DATABASE = {
    "anime.html": [],
    "game.html": [],
    "geek.html": [],
    "event.html": []
};

// Fetch categories from backend API and replace local DATABASE entries
// This function now supports server-side pagination: returns { items, page, total_pages, total_items }
async function fetchCategoryAPI(slug, page = 1, page_size = 10) {
    try {
        const lang = (() => {
            const current = getCurrentLang();
            if (current === 'jp') return 'ja';
            if (current === 'en' || current === 'ja' || current === 'id') return current;
            return 'id';
        })();
        const url = `/api/articles/${slug}/?page=${page}&page_size=${page_size}&lang=${encodeURIComponent(lang)}`;
        console.log(`[fetchCategoryAPI] Current lang: ${lang}, fetching from ${url}`);
        const res = await fetch(url);
        if (!res.ok) {
            console.error('Failed to fetch category', slug, res.status);
            return { items: [], page: 1, total_pages: 1, total_items: 0 };
        }
        const json = await res.json();
        const rawItems = Array.isArray(json.items) ? json.items : [];
        console.log(`[fetchCategoryAPI] Category ${slug} returned ${rawItems.length} items (page ${json.page}/${json.total_pages})`);
        if (rawItems.length > 0) {
            console.log(`[fetchCategoryAPI] Sample title:`, rawItems[0].title);
            console.log(`[fetchCategoryAPI] Sample URL:`, rawItems[0].url);
            if (rawItems[0].is_pinned) {
                console.log(`[fetchCategoryAPI] First item is PINNED`);
            }
        }
        const prefix = lang === 'id' ? '' : `/${lang}`;
        const mapped = rawItems.map(item => ({
            id: item.id,
            title: item.title,
            slug: item.slug,
            url: item.url || (item.slug ? `${prefix}/article/${item.slug}/` : null),
            category: item.category,
            img: item.img,
            desc: item.desc,
            is_pinned: item.is_pinned || false
        }));
        return { items: mapped, page: json.page || 1, total_pages: json.total_pages || 1, total_items: json.total_items || 0 };
    } catch (e) {
        console.error('Error fetching category', slug, e);
        return { items: [], page: 1, total_pages: 1, total_items: 0 };
    }
}

async function fetchPinnedArticle(apiSlug) {
    try {
        const lang = (() => {
            const current = getCurrentLang();
            if (current === 'jp') return 'ja';
            if (current === 'en' || current === 'ja' || current === 'id') return current;
            return 'id';
        })();
        const url = `/api/articles/${apiSlug}/pinned/?lang=${encodeURIComponent(lang)}`;
        console.log(`[fetchPinnedArticle] Current lang: ${lang}, fetching from ${url}`);
        const res = await fetch(url);
        if (!res.ok) return null;
        const json = await res.json();
        if (json && json.item) {
            console.log(`[fetchPinnedArticle] Pinned article title:`, json.item.title);
        }
        return json && json.item ? json.item : null;
    } catch (e) {
        console.error('fetchPinnedArticle error', e);
        return null;
    }
}

async function loadRemoteCategories() {
    // Note: DB category name is 'gaming' while the page path is '/game'.
    // Map the DB slug 'gaming' to the frontend key 'game.html' so /game works.
    const lang = getCurrentLang();
    console.log(`[loadRemoteCategories] Current language: ${lang}`);
    
    const mapping = { anime: 'anime.html', gaming: 'game.html', geek: 'geek.html', event: 'event.html' };
    const promises = Object.keys(mapping).map(async slug => {
        const resp = await fetchCategoryAPI(slug, 1, 10);
        const data = resp && resp.items ? resp.items : [];
        if (data && data.length > 0) DATABASE[mapping[slug]] = data;
    });
    await Promise.all(promises);
    // Log final counts
    Object.entries(mapping).forEach(([slug, key]) => {
        console.log(`[loadRemoteCategories] After load: ${key} has ${DATABASE[key].length} items`);
    });
}


// =========================================
// 4. LOGIKA RENDER HALAMAN KATEGORI
// =========================================

async function initNewsPage() {
    const heroContainer = document.getElementById('hero-section');
    if (!heroContainer) {
        console.log('[initNewsPage] No hero-section found, not a category page');
        return; // Bukan halaman kategori
    }

    // Derive slug from URL path. Example:
    // /anime/ -> ['anime'] -> slug = 'anime'
    // /en/anime/ -> ['en', 'anime'] -> slug = 'anime'
    const segments = window.location.pathname.split('/').filter(s => s.length > 0);
    
    // Remove language prefix if present
    const langPrefixes = ['en', 'ja', 'jp', 'id'];
    const filteredSegments = segments.filter(s => !langPrefixes.includes(s));
    
    const slug = filteredSegments.length ? filteredSegments[filteredSegments.length - 1] : 'index';
    console.log(`[initNewsPage] URL: ${window.location.pathname}`);
    console.log(`[initNewsPage] Segments: [${segments.join(', ')}]`);
    console.log(`[initNewsPage] Filtered: [${filteredSegments.join(', ')}]`);
    console.log(`[initNewsPage] Slug: ${slug}`);
    console.log(`[initNewsPage] Current language: ${getCurrentLang()}`);
    
    // Normalize UI slug to backend category name (handles /game -> 'gaming')
    const apiSlug = SLUG_TO_CATEGORY[slug] || slug;
    console.log(`[initNewsPage] API slug: ${apiSlug}`);
    
    // Let renderDynamicContent handle everything to avoid duplicate fetches
    // It will fetch data, render hero and grid properly
    await renderDynamicContent(1);
}

async function renderDynamicContent(page) {
    const subHeroContainer = document.getElementById('sub-hero-section');
    const gridContainer = document.getElementById('grid-section');
    if (!gridContainer) {
        console.warn('[renderDynamicContent] No grid-section found');
        return;
    }

    // request this page from server (normalize slug -> category)
    // Remove language prefixes before getting page slug
    const segments = window.location.pathname.split('/').filter(s => s.length > 0);
    const langPrefixes = ['en', 'ja', 'jp', 'id'];
    const filteredSegments = segments.filter(s => !langPrefixes.includes(s));
    const pageSlug = filteredSegments.length > 0 ? filteredSegments[filteredSegments.length - 1] : 'index';
    const apiPageSlug = SLUG_TO_CATEGORY[pageSlug] || pageSlug;
    
    console.log(`[renderDynamicContent] URL: ${window.location.pathname}`);
    console.log(`[renderDynamicContent] Page slug: ${pageSlug}, API slug: ${apiPageSlug}`);
    console.log(`[renderDynamicContent] Fetching page ${page}`);
    
    const resp = await fetchCategoryAPI(apiPageSlug, page, 10);
    console.log(`[renderDynamicContent] API response:`, resp);
    
    let items = resp.items || [];
    console.log(`[renderDynamicContent] Items count: ${items.length}`);
    
    // Fetch pinned article and ensure it becomes the hero on any page
    const pinned = await fetchPinnedArticle(apiPageSlug);
    if (pinned) {
        console.log(`[renderDynamicContent] Found pinned: ${pinned.title}`);
        // remove pinned from items if present to avoid duplicates
        items = items.filter(i => i.slug !== pinned.slug);
    }

    // First item on page -> hero; remaining -> grid
    // If pinned exists, use it as hero; otherwise first item on this page is hero
    const pageHero = pinned ? pinned : (items.length ? items[0] : null);
    const pageGrid = pinned ? items : (items.length > 1 ? items.slice(1) : []);

    console.log(`[renderDynamicContent] Grid items count: ${pageGrid.length}`);

    if (subHeroContainer) {
        subHeroContainer.classList.add('hidden');
        subHeroContainer.innerHTML = '';
    }
    
    // Render category grid using CardGrid (previous/default behavior)
    if (pageGrid.length > 0) {
        console.log(`[renderDynamicContent] Rendering ${pageGrid.length} items to grid`);
        gridContainer.innerHTML = pageGrid.map(item => CardGrid(item)).join('');
    } else {
        console.warn('[renderDynamicContent] No items to render in grid');
        gridContainer.innerHTML = `<div class="col-span-full text-center text-gray-500 italic" data-i18n="no.articles">No articles to display.</div>`;
    }

    // If on this page there's a hero, update hero container
    const heroContainer = document.getElementById('hero-section');
    if (heroContainer && pageHero) {
        console.log(`[renderDynamicContent] Rendering hero: ${pageHero.title}`);
        heroContainer.innerHTML = Hero(pageHero);
    }

    // render simple Next/Prev pagination controls
    renderPagination(resp.total_pages || 1, resp.page || 1);
    
    // Translate newly rendered content
    translatePage(getCurrentLang());
}

function renderPagination(totalPages, page) {
    const container = document.querySelector('.pagination-container');
    if (!container) return;
    const total = Math.max(1, totalPages);
    const curr = page || currentPage || 1;
    let html = '';

    html += `<button onclick="changePage(${curr - 1})" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-200 transition ${curr === 1 ? 'opacity-50 cursor-not-allowed' : ''}" ${curr === 1 ? 'disabled' : ''}><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg></button>`;

    for (let i = 1; i <= total; i++) {
        if (i === 1 || i === total || (i >= curr - 1 && i <= curr + 1)) {
            const activeClass = i === curr ? "bg-yellow-400 font-bold text-black" : "bg-gray-100 text-gray-600 hover:bg-gray-200";
            html += `<button onclick="changePage(${i})" class="w-8 h-8 flex items-center justify-center rounded transition ${activeClass}">${i}</button>`;
        } else if (i === curr - 2 || i === curr + 2) {
            html += `<span class="px-2 text-gray-400">...</span>`;
        }
    }

    html += `<button onclick="changePage(${curr + 1})" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-200 transition ${curr === total ? 'opacity-50 cursor-not-allowed' : ''}" ${curr === total ? 'disabled' : ''}><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg></button>`;

    container.innerHTML = html;
}

// Helper: get current article slug from URL
function getCurrentArticleSlug() {
    const segments = window.location.pathname.split('/').filter(s => s.length > 0);
    if (segments.length === 0) return null;
    if (segments[0] === 'article') return segments[1] || null;
    return segments[segments.length - 1] || null;
}

// Helper: collect one related article per category excluding the current article
function collectRelatedArticles(currentSlug) {
    // Only recommend these categories (remove 'event' from recommendations)
    const categories = ['anime', 'game', 'geek'];
    const mapKey = { anime: 'anime.html', game: 'game.html', geek: 'geek.html', event: 'event.html', gaming: 'game.html' };
    const related = [];

    categories.forEach(cat => {
        const key = mapKey[cat] || `${cat}.html`;
        const list = Array.isArray(DATABASE[key]) ? DATABASE[key] : [];
        if (!list.length) return;
        // find first item that is not the current article
        const found = list.find(it => {
            if (!it) return false;
            if (!currentSlug) return true; // no current slug -> accept first
            return (it.slug || it.id || '').toString() !== currentSlug.toString();
        });
        if (found) related.push(found);
    });

    return related;
}

window.changePage = function(page) {
    if (page < 1) return;
    currentPage = page;
    renderDynamicContent(page);
    
    const subHero = document.getElementById('sub-hero-section');
    const grid = document.getElementById('grid-section');
    const target = (page === 1 && subHero) ? subHero : grid; 
    if(target) {
        const y = target.getBoundingClientRect().top + window.scrollY - 100;
        window.scrollTo({top: y, behavior: 'smooth'});
    }
}

// [UPDATE] LOGIKA HALAMAN ARTIKEL
function initArticlePage() {
    const titleElement = document.getElementById('article-title');
    if (!titleElement) return; 

    // If server already rendered the article, do not overwrite its main content,
    // but still render "You may also like" recommendations client-side.
    const serverRendered = titleElement.dataset && titleElement.dataset.serverRendered === 'true';

    // If not server-rendered, fetch the article by slug from the API and populate DOM
    if (!serverRendered) {
        (async () => {
            // derive slug from path: /article/<slug>/
            const segments = window.location.pathname.split('/').filter(s => s.length > 0);
            const slug = segments.length && segments[0] === 'article' ? segments[1] : segments[segments.length - 1];
            if (!slug) return;
            try {
                const res = await fetch(`/api/article/${slug}/`);
                if (!res.ok) {
                    console.warn('Article API returned', res.status);
                    return;
                }
                const a = await res.json();
                // populate DOM
                titleElement.innerText = a.title || '';
                const catEl = document.getElementById('article-category');
                if (catEl) catEl.innerText = a.category || '';
                const imgEl = document.getElementById('article-image');
                if (imgEl) imgEl.src = (a.img || '/static/images/placeholder.png');
                const contentEl = document.querySelector('article.non-prose');
                if (contentEl) contentEl.innerHTML = a.content_html || a.content || '';

                // related: try to show some items from loaded DATABASE as before
                const relatedGrid = document.getElementById('related-news-grid');
                if (relatedGrid) {
                    const currentSlug = slug; // slug is already defined earlier in this async block
                    const relatedData = collectRelatedArticles(currentSlug);
                    relatedGrid.innerHTML = relatedData.map(item => CardGrid(item)).join('');
                }
            } catch (e) {
                console.error('Failed to fetch article by slug', e);
            }
        })();
    }

    console.log("Rendering Article Page...");

    // 1. KONTEN UTAMA (Client-side fallback only when not server-rendered)
    if (!serverRendered) {
        const articleData = DATABASE["anime.html"][0]; 
        if (articleData) {
            titleElement.innerText = articleData.title;
            const catEl = document.getElementById('article-category');
            if(catEl) catEl.innerText = articleData.category;
            const imgEl = document.getElementById('article-image');
            if(imgEl) imgEl.src = articleData.img.replace('../../', '/');
        }
    }

    // 2. RELATED NEWS (MIXED CATEGORY)
    const relatedGrid = document.getElementById('related-news-grid');
    if (relatedGrid) {
        const currentSlug = getCurrentArticleSlug();
        const relatedData = collectRelatedArticles(currentSlug);
        relatedGrid.innerHTML = relatedData.map(item => CardGrid(item)).join('');
    }
}
// =========================================
// 5. MAIN EXECUTION
// =========================================
document.addEventListener("DOMContentLoaded", async () => {
    console.debug('[main] DOMContentLoaded - script started');
    // 1. Load Layout (Navbar & Footer) and wait for navbar to be inserted
    await initLayout();
    
    // 1.5 Load remote categories from Django backend (if available)
    await loadRemoteCategories();

    // 1.6 Initialize client-side translations (bind language buttons) - AFTER navbar is loaded
    initI18n();
    
    // Expose i18n functions to global window for langRouter.js
    window.i18n = {
        translatePage: translatePage,
        getCurrentLang: getCurrentLang
    };
    
    // Small delay to ensure DOM is fully ready
    await new Promise(resolve => setTimeout(resolve, 100));
    translatePage(getCurrentLang());

    // log DATABASE counts for debugging
    try {
        Object.entries(DATABASE).forEach(([k,v]) => console.debug('[main] DATABASE', k, 'count=', Array.isArray(v)?v.length:0));
    } catch(e) { console.debug('[main] DATABASE debug error', e); }

    // 2. Load Homepage Content
    renderHeroSlides(); 
    initHeroSlider(); 
    initHomepage();
    translatePage(getCurrentLang());

    // 3. Load Category Page Content
    initNewsPage();
    await new Promise(resolve => setTimeout(resolve, 50));
    translatePage(getCurrentLang());
    
    initArticlePage();
});