const CACHE_NAME = "retro-cache-v1";

const urlsToCache = [
    "/",
    "/offline",
    "/static/style.css",
    "/static/offline/natsuki.png"
];

self.addEventListener("install", event => {

    event.waitUntil(

        caches.open(CACHE_NAME)

        .then(cache => {

            return cache.addAll(urlsToCache);

        })
    );
});

self.addEventListener("fetch", event => {

    event.respondWith(

        fetch(event.request)

        .catch(() => {

            return caches.match("/offline");

        })
    );
});