// Fungsi Utama
export function initLayout() {
    // 1. Load Komponen & Tunggu selesai, return promise so caller can await
    const p = Promise.all([loadNavbar(), loadFooter()]).then(() => {
        // 2. Setelah semua siap, baru munculkan halaman (Fade In)
        revealPage();
    });

    // 3. Aktifkan efek keluar saat klik link (Fade Out)
    initPageTransition();
    return p;
}
function revealPage() {
    requestAnimationFrame(() => {
    document.body.classList.add('loaded');
});
}

// --- ANIMASI PINDAH HALAMAN (SPA FEEL) ---
function initPageTransition() {
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        
        if (
            link &&
            link.href.startsWith(window.location.origin) && // hanya link internal
            link.target !== '_blank' &&                     // bukan tab baru
            !link.hasAttribute('download') &&               // bukan file download
            link.pathname !== window.location.pathname      // bukan halaman yang sama
        ) {
            e.preventDefault();

            // Fade Out
            document.body.classList.remove('loaded');

            // Setelah animasi selesai, pindah halaman
            setTimeout(() => {
                window.location.href = link.href;
            }, 400);
        }
    });

    // Tambahkan fade-in saat halaman selesai dimuat
    window.addEventListener('load', () => {
        document.body.classList.add('loaded');
    });
}

function loadNavbar() {
    return fetch('/static/html/components/Navbar.html')
        .then(r => r.text())
        .then(h => {
            const nav = document.getElementById('navbar-placeholder');
            if (nav) {
                nav.innerHTML = h;
                initNavbarDropdown();
                initMobileMenu();
                setActiveNavbarItem();
            }
        });
}

function loadFooter() {
    return fetch('/static/html/components/Footer.html')
        .then(r => r.text())
        .then(h => {
            const foot = document.getElementById('footer-placeholder');
            if (foot) foot.innerHTML = h;
        });
}



function initNavbarDropdown() {
    const langBtn = document.getElementById("langBtn");
    const langDropdown = document.getElementById("langDropdown");
    if (!langBtn || !langDropdown) return;
    langBtn.addEventListener("click", () => langDropdown.classList.toggle("hidden"));
    window.addEventListener("click", (e) => {
        if (!langBtn.contains(e.target) && !langDropdown.contains(e.target)) 
            langDropdown.classList.add("hidden");
    });
}
function initMobileMenu() {
    const openBtn = document.getElementById('mobile-menu-btn');
    const closeBtn = document.getElementById('close-menu-btn');
    const menu = document.getElementById('mobile-menu');
    const backdrop = document.getElementById('mobile-menu-backdrop');

    function open() {
        if (menu && backdrop) {
            backdrop.classList.remove('hidden');
            menu.classList.remove('translate-x-full');
            document.body.style.overflow = 'hidden';
        }
    }
    function close() {
        if (menu && backdrop) {
            backdrop.classList.add('hidden');
            menu.classList.add('translate-x-full');
            document.body.style.overflow = 'auto';
        }
    }

    if (openBtn) openBtn.addEventListener('click', open);
    if (closeBtn) closeBtn.addEventListener('click', close);
    if (backdrop) backdrop.addEventListener('click', close);
}
function setActiveNavbarItem() {
    // Normalize current path to a key used in nav hrefs.
    // Examples:
    //  - '/' -> 'index'
    //  - '/anime/' or '/anime' -> 'anime'
    //  - '/article/some-slug/' -> 'article/some-slug' (we'll match by startsWith)
    let rawPath = window.location.pathname || '/';
    // remove leading and trailing slashes
    let normalized = rawPath.replace(/^\/+|\/+$/g, '');
    if (normalized === '') normalized = 'index';

    console.log('Halaman Aktif (normalized):', normalized);

    // Helper: normalize href values to comparable keys
    const normalizeHref = (href) => {
        if (!href) return '';
        // If absolute URL, extract pathname
        try {
            const url = new URL(href, window.location.origin);
            href = url.pathname;
        } catch (e) {
            // href might be a relative path like 'anime.html' or '/anime'
        }
        let h = href.replace(/^\/+|\/+$/g, '');
        // remove .html extension if present
        h = h.replace(/\.html$/i, '');
        if (h === '') h = 'index';
        return h;
    };

    // 1. Desktop Active State
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        const key = normalizeHref(href);

        // consider a match when normalized keys are equal OR when current path starts with key
        if (key && (key === normalized || normalized.startsWith(key + '/') || (key === 'index' && normalized === 'index'))) {
            item.classList.add('bg-[#EFED3C]', 'text-[#000000CC]', 'shadow-lg', 'font-semibold');
            item.classList.remove('bg-white', 'text-gray-700');
        } else {
            // ensure non-active items keep default styles
            item.classList.remove('bg-[#EFED3C]', 'text-[#000000CC]', 'shadow-lg', 'font-semibold');
            item.classList.add('bg-white', 'text-gray-700');
        }
    });

    // 2. Mobile Active State
    document.querySelectorAll('.nav-item-mobile').forEach(item => {
        const href = item.getAttribute('href');
        const key = normalizeHref(href);

        if (key && (key === normalized || normalized.startsWith(key + '/'))) {
            item.classList.remove('border-gray-200', 'text-gray-700', 'hover:bg-gray-50');
            item.classList.add('border-[#EFED3C]', 'border-l-4', 'bg-yellow-50', 'text-black', 'font-bold');
        } else {
            item.classList.remove('border-[#EFED3C]', 'border-l-4', 'bg-yellow-50', 'text-black', 'font-bold');
            item.classList.add('border-gray-200', 'text-gray-700', 'hover:bg-gray-50');
        }
    });
}