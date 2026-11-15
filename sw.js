/* Kanji Radical Map — offline-first service worker (same-origin only)
 * Documents are network-first so the viewer always shows the latest version;
 * everything else is cache-first with fetch fallback for offline use. */
var CACHE = 'kanji-radical-map-v2';
var ASSETS = [
  'index.html',
  'manifest.json',
  'docs/icon-192.png',
  'docs/icon-512.png',
  'docs/icon-maskable-512.png'
];

self.addEventListener('install', function (e) {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(function (cache) { return cache.addAll(ASSETS); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
        return null;
      })).then(function () { return self.clients.claim(); });
    })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Documents: network first, cache fallback (offline).
  var isDocument = req.destination === 'document' ||
    url.pathname === '/' ||
    url.pathname.endsWith('/index.html');
  if (isDocument) {
    e.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (cache) { cache.put('index.html', copy); });
        }
        return res;
      }).catch(function () {
        return caches.match('index.html', { ignoreSearch: true });
      })
    );
    return;
  }

  // Static assets: cache first, fetch fallback (and populate the cache).
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(function (cached) {
      if (cached) return cached;
      return fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (cache) { cache.put(req, copy); });
        }
        return res;
      });
    })
  );
});
