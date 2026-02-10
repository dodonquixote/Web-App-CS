// Kita Import CardGrid karena desain kartu kanan SAMA dengan grid bawah
import { CardGrid } from './CardGrid.js'; 

export function SubHero(leftData, rightData) {
    
    // Detect current language from URL and build prefix
    const path = window.location.pathname;
    const pathMatch = path.match(/^(\/(en|jp|ja|id))?/);
    const currentLang = pathMatch && pathMatch[2] ? pathMatch[2] : 'id';
    const normalizedLang = currentLang === 'jp' ? 'ja' : currentLang;
    const prefix = normalizedLang === 'id' ? '' : `/${normalizedLang}`;
    
    // Use leftData.url if available (already has prefix from backend), otherwise build URL with prefix
    const leftArticleUrl = leftData.url || (leftData.slug ? `${prefix}/article/${leftData.slug}/` : '#');
    
    // HTML untuk kartu kanan menggunakan komponen yang sudah ada
    const rightCardHTML = CardGrid(rightData);

    return `
    <div class="bg-white border border-gray-200 rounded-xl overflow-hidden flex shadow-sm hover:shadow-md transition relative group h-56">
        
        <div class="w-1/2 relative overflow-hidden">
            <img src="${leftData.img}" 
                 alt="${leftData.title}" 
                 class="w-full h-full object-cover transition duration-500 group-hover:scale-110">
        </div>
        
        <div class="w-1/2 p-6 flex flex-col justify-between">
            <div>
                <div class="flex items-center gap-2 mb-2">
                    <h3 class="font-bold text-lg leading-tight line-clamp-2">
                        ${leftData.title}
                    </h3>
                    <span class="bg-yellow-400 text-black text-[10px] font-bold px-2 py-0.5 rounded">
                        ${leftData.category}
                    </span>
                </div>
                <div class="text-xs text-gray-500 line-clamp-3">
                    ${leftData.desc_html || leftData.desc}
                </div>
            </div>
            
            <div class="flex items-center text-gray-400 text-xs mt-4">
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                DD/MM/YYYY
            </div>
        </div>
        
        <a href="${leftArticleUrl}" class="absolute inset-0 z-10"></a>
    </div>

    ${rightCardHTML}
    `;
}