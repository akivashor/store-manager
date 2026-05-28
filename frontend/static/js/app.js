const API = "";
let token = localStorage.getItem("token");
let cashier = JSON.parse(localStorage.getItem("cashier") || "null");
let cart = [];
let products = [];

// ── Auth ────────────────────────────────────────────────────────────────────

document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const body = new URLSearchParams({
    username: document.getElementById("email").value,
    password: document.getElementById("password").value,
  });
  const res = await fetch(`${API}/api/auth/login`, { method: "POST", body });
  const err = document.getElementById("login-error");
  if (!res.ok) {
    err.textContent = "Invalid email or password";
    err.classList.remove("hidden");
    return;
  }
  const data = await res.json();
  token = data.access_token;
  cashier = data.cashier;
  localStorage.setItem("token", token);
  localStorage.setItem("cashier", JSON.stringify(cashier));
  showApp();
});

function logout() {
  localStorage.clear();
  token = null; cashier = null; cart = [];
  document.getElementById("app").classList.add("hidden");
  document.getElementById("login-screen").classList.remove("hidden");
}

// ── App Init ─────────────────────────────────────────────────────────────────

async function showApp() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  document.getElementById("cashier-info").textContent = `${cashier.name} · ${cashier.cashier_code}`;
  if (cashier.is_admin) {
    document.getElementById("add-product-btn-wrap").classList.remove("hidden");
  }
  await loadProducts();
  showTab("pos");
  registerServiceWorker();
}

if (token && cashier) showApp();

// ── API helper ───────────────────────────────────────────────────────────────

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (res.status === 401) { logout(); return null; }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return { _error: err.detail || `Error ${res.status}` };
  }
  return res.json();
}

// ── Tabs ─────────────────────────────────────────────────────────────────────

function showTab(tab) {
  ["pos", "products", "stock", "sales"].forEach(t => {
    document.getElementById(`tab-content-${t}`).classList.toggle("hidden", t !== tab);
    const btn = document.getElementById(`tab-${t}`);
    btn.classList.toggle("text-blue-400", t === tab);
    btn.classList.toggle("border-b-2", t === tab);
    btn.classList.toggle("border-blue-400", t === tab);
    btn.classList.toggle("text-slate-400", t !== tab);
  });
  if (tab === "stock") loadStock();
  if (tab === "sales") loadSales();
  if (tab === "products") renderProductList();
}

// ── Products ─────────────────────────────────────────────────────────────────

async function loadProducts() {
  products = await api("/api/products") || [];
  renderPOSProducts();
}

function renderPOSProducts() {
  document.getElementById("product-list-pos").innerHTML = products.map(p => `
    <button onclick='addToCart(${p.id})' class="bg-slate-800 rounded-xl p-3 text-left hover:bg-slate-700 transition">
      <p class="font-medium text-sm truncate">${p.name}</p>
      <p class="text-green-400 text-sm">$${parseFloat(p.price).toFixed(2)}</p>
      <p class="text-xs text-slate-400">${p.stock ? p.stock.quantity : 0} in stock</p>
    </button>
  `).join("");
}

function renderProductList() {
  document.getElementById("product-list").innerHTML = products.map(p => `
    <div class="bg-slate-800 rounded-xl p-4">
      <div class="flex justify-between items-start">
        <div>
          <p class="font-semibold">${p.name}</p>
          <p class="text-slate-400 text-sm">${p.category || "Uncategorized"}</p>
          ${p.barcode ? `<p class="text-xs text-slate-500">Barcode: ${p.barcode}</p>` : ""}
        </div>
        <span class="text-green-400 font-bold">$${parseFloat(p.price).toFixed(2)}</span>
      </div>
      <div class="mt-2 flex gap-3 text-sm">
        <span class="${(p.stock?.quantity || 0) <= (p.stock?.min_quantity || 5) ? 'text-red-400' : 'text-slate-300'}">
          Stock: ${p.stock?.quantity ?? 0}
        </span>
        <span class="text-slate-500">Min: ${p.stock?.min_quantity ?? 5}</span>
      </div>
    </div>
  `).join("");
}

// ── Add Product ───────────────────────────────────────────────────────────────

function toggleAddProduct() {
  const form = document.getElementById("add-product-form");
  form.classList.toggle("hidden");
  document.getElementById("np-error").classList.add("hidden");
}

async function submitAddProduct() {
  const name = document.getElementById("np-name").value.trim();
  const price = document.getElementById("np-price").value;
  const errEl = document.getElementById("np-error");

  if (!name || !price) {
    errEl.textContent = "Name and price are required.";
    errEl.classList.remove("hidden");
    return;
  }

  const params = new URLSearchParams({
    initial_stock: document.getElementById("np-stock").value || 0,
    min_quantity: document.getElementById("np-min-stock").value || 5,
  });

  const product = await api(`/api/products?${params}`, {
    method: "POST",
    body: JSON.stringify({
      name,
      price: parseFloat(price),
      category: document.getElementById("np-category").value.trim() || null,
      barcode: document.getElementById("np-barcode").value.trim() || null,
    }),
  });

  if (!product || product._error) {
    errEl.textContent = product?._error || "Failed to create product.";
    errEl.classList.remove("hidden");
    return;
  }

  ["np-name", "np-price", "np-category", "np-barcode"].forEach(id => document.getElementById(id).value = "");
  document.getElementById("np-stock").value = "0";
  document.getElementById("np-min-stock").value = "5";
  toggleAddProduct();
  await loadProducts();
  renderProductList();
}

// ── POS / Cart ────────────────────────────────────────────────────────────────

function addToCart(productId) {
  const product = products.find(p => p.id === productId);
  if (!product || !product.stock || product.stock.quantity === 0) return;
  const existing = cart.find(i => i.product_id === productId);
  if (existing) {
    if (existing.quantity < product.stock.quantity) existing.quantity++;
  } else {
    cart.push({ product_id: productId, quantity: 1, name: product.name, price: parseFloat(product.price) });
  }
  renderCart();
}

function removeFromCart(productId) {
  cart = cart.filter(i => i.product_id !== productId);
  renderCart();
}

function renderCart() {
  const cartEl = document.getElementById("cart");
  const totalEl = document.getElementById("cart-total");
  if (cart.length === 0) {
    cartEl.innerHTML = '<p class="text-slate-500 text-sm text-center py-8">Tap a product to add it to the sale</p>';
    totalEl.classList.add("hidden");
    return;
  }
  const total = cart.reduce((s, i) => s + i.price * i.quantity, 0);
  cartEl.innerHTML = cart.map(i => `
    <div class="bg-slate-800 rounded-xl px-4 py-3 flex justify-between items-center">
      <div>
        <p class="font-medium text-sm">${i.name}</p>
        <p class="text-slate-400 text-xs">$${i.price.toFixed(2)} × ${i.quantity}</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-green-400 font-semibold">$${(i.price * i.quantity).toFixed(2)}</span>
        <button onclick="removeFromCart(${i.product_id})" class="text-red-400 hover:text-red-300 text-lg leading-none">×</button>
      </div>
    </div>
  `).join("");
  document.getElementById("total-amount").textContent = `$${total.toFixed(2)}`;
  totalEl.classList.remove("hidden");
}

function clearCart() { cart = []; renderCart(); }

async function submitSale() {
  if (cart.length === 0) return;
  const sale = await api("/api/sales", {
    method: "POST",
    body: JSON.stringify({ items: cart.map(i => ({ product_id: i.product_id, quantity: i.quantity })) }),
  });
  if (sale) {
    clearCart();
    await loadProducts();
    alert(`Sale #${sale.id} completed — $${parseFloat(sale.total_amount).toFixed(2)}`);
  }
}

// ── Stock ─────────────────────────────────────────────────────────────────────

async function loadStock() {
  const lowStock = await api("/api/products/low-stock") || [];
  const lowStockAlert = document.getElementById("low-stock-alert");
  if (lowStock.length > 0) {
    lowStockAlert.classList.remove("hidden");
    document.getElementById("low-stock-list").innerHTML = lowStock.map(p =>
      `<p>• ${p.name} — <span class="text-red-400">${p.stock?.quantity ?? 0} left</span></p>`
    ).join("");
  } else {
    lowStockAlert.classList.add("hidden");
  }

  document.getElementById("stock-list").innerHTML = products.map(p => `
    <div class="bg-slate-800 rounded-xl p-4 flex justify-between items-center">
      <div>
        <p class="font-semibold">${p.name}</p>
        <p class="text-slate-400 text-xs">Min: ${p.stock?.min_quantity ?? 5}</p>
      </div>
      <span class="text-2xl font-bold ${(p.stock?.quantity || 0) <= (p.stock?.min_quantity || 5) ? 'text-red-400' : 'text-green-400'}">
        ${p.stock?.quantity ?? 0}
      </span>
    </div>
  `).join("");
}

// ── Sales ─────────────────────────────────────────────────────────────────────

async function loadSales() {
  const sales = await api("/api/sales/my") || [];
  document.getElementById("sales-list").innerHTML = sales.length === 0
    ? '<p class="text-slate-500 text-sm text-center py-8">No sales yet</p>'
    : sales.map(s => `
      <div class="bg-slate-800 rounded-xl p-4">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm text-slate-400">Sale #${s.id}</span>
          <span class="text-green-400 font-bold">$${parseFloat(s.total_amount).toFixed(2)}</span>
        </div>
        <p class="text-xs text-slate-500">${new Date(s.created_at).toLocaleString()}</p>
        <div class="mt-2 space-y-1">
          ${s.items.map(i => `<p class="text-xs text-slate-400">· ${i.quantity}× product #${i.product_id} @ $${parseFloat(i.unit_price).toFixed(2)}</p>`).join("")}
        </div>
      </div>
    `).join("");
}

// ── PWA / Push ────────────────────────────────────────────────────────────────

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  const reg = await navigator.serviceWorker.register("/sw.js");
  const keyData = await api("/api/notifications/vapid-public-key");
  if (!keyData?.public_key) return;
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: keyData.public_key,
  });
  await api("/api/notifications/subscribe", { method: "POST", body: JSON.stringify(sub) });
}
