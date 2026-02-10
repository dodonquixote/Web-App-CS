export function CardHome(data) {
    // Detect current language from URL and build prefix
    const path = window.location.pathname;
    const pathMatch = path.match(/^(\/(en|jp|ja|id))?/);
    const currentLang = pathMatch && pathMatch[2] ? pathMatch[2] : 'id';
    const normalizedLang = currentLang === 'jp' ? 'ja' : currentLang;
    const prefix = normalizedLang === 'id' ? '' : `/${normalizedLang}`;
    
    // Use data.url if available (already has prefix from backend), otherwise build URL with prefix
    const articleUrl = data.url || (data.slug ? `${prefix}/article/${data.slug}/` : '#');
    
    return `
    <div class="min-w-[85%] md:min-w-0 w-full bg-white rounded-[15px] shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 group relative snap-center border border-gray-100">
        
        <div class="relative h-[180px] md:h-[180px] w-full">
            <img src="${data.img}" 
                 alt="${data.title}"
                 class="w-full h-full object-cover rounded-t-[15px] transition duration-500 group-hover:scale-110">

            <div class="absolute bottom-0 left-0 w-full bg-black/40 px-5 py-4 rounded-b-[15px]">
                <span class="absolute -top-3 left-5 bg-[#EFED3C] text-black text-[10px] font-bold px-3 py-0.5 rounded-full shadow-sm uppercase">
                    ${data.category}
                </span>

                <h2 class="text-white text-[18px] md:text-[25px] font-medium leading-tight line-clamp-1 mt-1">
                    ${data.title}
                </h2>
            </div>
        </div>

        <div class="p-5 hidden md:block">
            <div class="text-gray-700 text-[20px] font-medium leading-relaxed line-clamp-2 break-long-words">
                ${data.desc_html || data.desc}
            </div>
        </div>
        
        <div class="p-4 md:hidden block">
             <div class="text-gray-600 text-sm line-clamp-2">
                ${data.desc_html || data.desc}
            </div>
        </div>

        <a href="${articleUrl}" class="absolute inset-0 z-10"></a>
    </div>
    `;
}