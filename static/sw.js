/**
 * sw.js – Service Worker para PowderyVision7 PWA
 *
 * Estrategia:
 *   - Recursos estáticos (CSS, iconos, manifest): cache-first
 *   - Página principal GET /: network-first, fallback a cache, luego offline
 *   - POST (análisis de imagen): siempre red (requiere servidor)
 */

const CACHE_NAME = 'powderyvision-v1';

// Recursos que se guardan al instalar el SW
const PRECACHE_ASSETS = [
  '/static/css/style.css',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
];

// ── Página offline embebida (se muestra sin red y sin caché) ───────────────
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PowderyVision7 – Sin conexión / Offline</title>
  <style>
    body {
      font-family: sans-serif;
      background: #f0f4f0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
      padding: 20px;
      text-align: center;
      color: #333;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 32px 24px;
      max-width: 420px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    h1 { color: #4CAF50; font-size: 1.6rem; margin-bottom: 8px; }
    p  { line-height: 1.6; }
    .icon { font-size: 4rem; margin-bottom: 16px; }
    button {
      margin-top: 20px;
      background: #4CAF50;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 12px 28px;
      font-size: 1rem;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">🌿📡</div>
    <h1>PowderyVision7</h1>
    <p>
      <strong>Sin conexión a internet / No internet connection</strong>
    </p>
    <p>
      El análisis de imágenes requiere conexión al servidor.<br>
      Conéctate a internet e inténtalo de nuevo.
    </p>
    <p style="font-size:0.9rem; color:#777;">
      Image analysis requires a connection to the server.<br>
      Please connect to the internet and try again.
    </p>
    <button onclick="location.reload()">🔄 Reintentar / Retry</button>
  </div>
</body>
</html>`;

// ── INSTALL: pre-cachear recursos estáticos ────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_ASSETS).catch(() => {
        // Si algún recurso falla (ej. iconos aún no generados), continuar igual
      });
    }).then(() => self.skipWaiting())
  );
});

// ── ACTIVATE: eliminar cachés viejas ──────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── FETCH: lógica de red ───────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // POST (envío de imagen para análisis): siempre red, nunca caché
  if (request.method === 'POST') {
    return; // deja pasar al navegador normalmente
  }

  // Recursos estáticos: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, clone));
          return response;
        });
      })
    );
    return;
  }

  // Páginas HTML (navegación): network-first, fallback a offline
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Guardar en caché la respuesta de la página principal
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(c => c.put(request, clone));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then(cached =>
            cached || new Response(OFFLINE_HTML, {
              headers: { 'Content-Type': 'text/html; charset=utf-8' }
            })
          )
        )
    );
    return;
  }
});
