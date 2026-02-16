const CACHE_NAME = 'zeittracker-v8';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/login.html',
    '/css/styles.css',
    '/css/login.css',
    '/js/app.js',
    '/js/api.js',
    '/js/auth.js',
    '/js/i18n.js',
    '/js/utils.js',
    '/js/timer.js',
    '/js/calendar.js',
    '/js/entries.js',
    '/js/reports.js',
    '/js/overtime.js',
    '/js/admin.js',
    '/manifest.json',
    '/icons/icon.svg'
];

// Install - cache static assets for offline fallback
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate - clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch - network-first for everything, cache as offline fallback
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // API requests: network only (no caching)
    if (url.pathname.startsWith('/api/')) {
        return;
    }

    // Static assets: network-first, fallback to cache (offline support)
    event.respondWith(
        fetch(event.request).then(response => {
            // Update cache with fresh response
            if (response.ok && response.type === 'basic') {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, clone);
                });
            }
            return response;
        }).catch(() => {
            // Offline: serve from cache
            return caches.match(event.request).then(cached => {
                if (cached) return cached;
                // Offline fallback for navigation
                if (event.request.mode === 'navigate') {
                    return caches.match('/index.html');
                }
            });
        })
    );
});
