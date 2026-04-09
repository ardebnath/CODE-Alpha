const CACHE_NAME = "alpha-studio-v6";
const SHELL_PATHS = new Set([
    "/",
    "/index.html",
    "/style.css",
    "/studio.js",
    "/manifest.webmanifest",
]);
const ASSETS = [
    "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                    return Promise.resolve();
                })
            )
        )
    );
    self.clients.claim();
});

self.addEventListener("message", (event) => {
    if (event.data && event.data.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});

self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") {
        return;
    }

    const requestUrl = new URL(event.request.url);

    // API responses should always come from the network so Starter Programs,
    // package lists, and run history stay fresh after updates.
    if (requestUrl.origin === self.location.origin && requestUrl.pathname.startsWith("/api/")) {
        event.respondWith(fetch(event.request, { cache: "no-store" }));
        return;
    }

    if (
        requestUrl.origin === self.location.origin &&
        (event.request.mode === "navigate" || SHELL_PATHS.has(requestUrl.pathname))
    ) {
        event.respondWith(
            fetch(event.request, { cache: "no-store" })
                .then((networkResponse) => {
                    if (networkResponse.status === 200 && networkResponse.type === "basic") {
                        const clone = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    }
                    return networkResponse;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(event.request).then((networkResponse) => {
                if (networkResponse.status === 200 && networkResponse.type === "basic") {
                    const clone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return networkResponse;
            });
        })
    );
});
