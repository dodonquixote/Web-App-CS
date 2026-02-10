// Helper function to truncate text to max characters
function truncateText(text, maxChars = 250) {
    if (!text) return '';
    if (text.length <= maxChars) return text;
    return text.substring(0, maxChars) + '...';
}

export function Hero(data) {
    // Detect current language from URL and build prefix
    const path = window.location.pathname;
    const pathMatch = path.match(/^(\/(en|jp|ja|id))?/);
    const currentLang = pathMatch && pathMatch[2] ? pathMatch[2] : 'id';
    const normalizedLang = currentLang === 'jp' ? 'ja' : currentLang;
    const prefix = normalizedLang === 'id' ? '' : `/${normalizedLang}`;
    
    // Use data.url if available (already has prefix from backend), otherwise build URL with prefix
    const articleUrl = data.url || (data.slug ? `${prefix}/article/${data.slug}/` : '#');
    
    // Truncate description to prevent overflow
    const descText = data.desc || '';
    const truncatedDesc = truncateText(descText, 250);
    
    return `
    <div class="relative rounded-xl aspect-video overflow-hidden mb-8 group shadow-lg bg-black lg scale-90">
        <img src="${data.img}" alt="${data.title}" class="w-full h-full object-cover">
        
        <div class="absolute bottom-0 md:top-0 right-0 h-1/2 md:h-full w-full md:w-1/3 bg-black/80 md:bg-gray-900/90 p-8 flex flex-col justify-center text-white backdrop-blur-sm md:backdrop-blur-none">
            <h2 class="text-lg md:text-3xl font-extrabold uppercase mb-4 tracking-wide leading-tight">
                ${data.title}
            </h2>
            <p class="text-gray-300 text-xs md:text-sm leading-relaxed line-clamp-3">
                ${truncatedDesc}
            </p>
        </div>
        <a href="${articleUrl}" class="absolute inset-0 z-10"></a>
    </div>
    `;
}