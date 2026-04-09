const CACHE_NAME = "alpha-web-engine-v1";
const SHELL_FILES = [
    "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES))
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

self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") {
        return;
    }

    const requestUrl = new URL(event.request.url);
    if (requestUrl.origin === self.location.origin && requestUrl.pathname.startsWith("/api/")) {
        event.respondWith(fetch(event.request, { cache: "no-store" }));
        return;
    }

    event.respondWith(
        fetch(event.request, { cache: "no-store" }).catch(() => caches.match(event.request))
    );
});
