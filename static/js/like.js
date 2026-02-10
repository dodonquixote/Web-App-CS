// Minimal like widget: client-only, stores counts in localStorage per-article
document.addEventListener('DOMContentLoaded', function () {
  try {
    const container = document.getElementById('likeSection');
    if (!container) return;
    const slug = container.dataset.slug;
    if (!slug) {
      // Nothing to like for pages without slug
      container.style.display = 'none';
      return;
    }

    const likeKey = `likes:${slug}`;
    const likedKey = `liked:${slug}`;

    // Read stored values
    let count = parseInt(localStorage.getItem(likeKey) || '0', 10);
    let liked = localStorage.getItem(likedKey) === '1';

    // Build UI
    const wrapper = document.createElement('div');
    wrapper.className = 'flex items-center gap-2';

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white border border-gray-200 hover:bg-gray-50 text-sm';
    btn.setAttribute('aria-pressed', liked ? 'true' : 'false');

    const icon = document.createElement('span');
    icon.innerHTML = liked ? '❤️' : '🤍';
    icon.className = 'text-lg';

    const txt = document.createElement('span');
    txt.className = 'text-sm text-gray-800 font-medium';
    txt.textContent = count.toString();

    btn.appendChild(icon);
    btn.appendChild(txt);

    btn.addEventListener('click', function () {
      if (liked) {
        count = Math.max(0, count - 1);
        liked = false;
        icon.innerHTML = '🤍';
        btn.setAttribute('aria-pressed', 'false');
      } else {
        count = count + 1;
        liked = true;
        icon.innerHTML = '❤️';
        btn.setAttribute('aria-pressed', 'true');
      }
      txt.textContent = count.toString();
      try {
        localStorage.setItem(likeKey, String(count));
        localStorage.setItem(likedKey, liked ? '1' : '0');
      } catch (err) {
        console.warn('like widget storage failed', err);
      }

      // TODO: optionally POST to server endpoint to persist likes
    });

    wrapper.appendChild(btn);
    container.appendChild(wrapper);
  } catch (err) {
    console.warn('like widget init failed', err);
  }
});
