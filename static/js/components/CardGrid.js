export function CardGrid(data) {
    // Detect current language from URL and build prefix
    const path = window.location.pathname;
    const pathMatch = path.match(/^(\/(en|jp|ja|id))?/);
    const currentLang = pathMatch && pathMatch[2] ? pathMatch[2] : 'id';
    const normalizedLang = currentLang === 'jp' ? 'ja' : currentLang;
    const prefix = normalizedLang === 'id' ? '' : `/${normalizedLang}`;
    
    // Use data.url if available (already has prefix from backend), otherwise build URL with prefix
    const articleUrl = data.url || (data.slug ? `${prefix}/article/${data.slug}/` : '#');
    
    return `
   <div class="relative rounded-[15px] overflow-hidden h-56 group cursor-pointer shadow-lg hover:scale-[1.02] transition-transform duration-300">

        <img src="${data.img}"
             alt="${data.title}"
             class="w-full h-full object-cover rounded-[15px] transition duration-500 group-hover:scale-110">

        <div class="absolute bottom-0 left-0 w-full bg-black/40 px-5 py-5 rounded-b-[15px]">
            <span class="absolute -top-3 left-5 bg-yellow-400 text-black text-[10px] font-semibold px-3 py-1 rounded-full shadow">
                ${data.category}
            </span>
            <h3 class="text-white font-bold text-lg leading-tight mt-2 line-clamp-2">
                ${data.title}
            </h3>
            <div class="text-[11px] text-gray-200 mt-1 leading-snug line-clamp-2 break-long-words">
                ${data.desc_html || data.desc}
            </div>
        </div>

        <a href="${articleUrl}" class="absolute inset-0 z-10"></a>
    </div>
    `;
}