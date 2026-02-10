// Update all navigation links to include language prefix
(function() {
    function updateLinksWithLanguage() {
        const path = window.location.pathname;
        
        // Detect current language from URL
        const pathMatch = path.match(/^(\/(en|jp|ja|id))?(.*)$/);
        const currentLang = pathMatch && pathMatch[2] ? pathMatch[2] : 'id';
        
        // Normalize ja/jp
        const normalizedLang = currentLang === 'jp' ? 'ja' : currentLang;
        
        // Create prefix
        const prefix = normalizedLang === 'id' ? '' : `/${normalizedLang}`;
        
        // Sync language to localStorage
        localStorage.setItem('lang', normalizedLang);
        
        // Translate static text on the page based on URL language
        if (window.i18n && typeof window.i18n.translatePage === 'function') {
            window.i18n.translatePage(normalizedLang);
            console.log('[langRouter] Translated page to:', normalizedLang);
        }
        
        // Update all navigation links
        const navLinks = document.querySelectorAll('a.nav-item, a.nav-item-mobile, a[href^="/"]');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#') || href.startsWith('http') || href.includes('/admin') || href.includes('/dashboard') || href.includes('/api/')) {
                return; // Skip external, hash, admin, dashboard and API links
            }
            
            // Remove existing language prefix if present
            const cleanHref = href.replace(/^\/(en|jp|ja|id)/, '');
            
            // Add current language prefix
            const newHref = prefix + (cleanHref || '/');
            link.setAttribute('href', newHref);
        });
        
        console.log('[langRouter] Updated navigation links with prefix:', prefix);
    }
    
    // Update on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateLinksWithLanguage);
    } else {
        updateLinksWithLanguage();
    }
    
    // Also update when navbar is loaded dynamically
    const observer = new MutationObserver((mutations) => {
        const hasNewLinks = mutations.some(m => {
            return Array.from(m.addedNodes).some(node => {
                if (node.nodeType === 1) {
                    return node.tagName === 'A' || node.querySelector('a');
                }
                return false;
            });
        });
        
        if (hasNewLinks) {
            updateLinksWithLanguage();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
