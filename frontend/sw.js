const CACHE = "store-v1";
const ASSETS = ["/", "/index.html", "/static/js/app.js"];

self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS))));
self.addEventListener("fetch", e => e.respondWith(
  caches.match(e.request).then(r => r || fetch(e.request))
));
self.addEventListener("push", e => {
  const data = e.data ? e.data.json() : { title: "Store Manager", body: "Notification" };
  e.waitUntil(self.registration.showNotification(data.title, { body: data.body, icon: "/static/icon-192.png" }));
});
