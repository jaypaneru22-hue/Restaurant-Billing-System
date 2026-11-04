/**
 * RestoPro — Client Controller for Responsive Mobile Web Portal
 * Independent multi-customer sessions, real-time order tracking, and cart management.
 */

const App = (() => {
  const API_BASE = "";
  const TOKEN_KEY = "restopro_session_token";
  const TABLE_KEY = "restopro_selected_table";
  const ACTIVE_ORDER_KEY = "restopro_active_order_id";

  let currentUser = null;
  let allMenuItems = [];
  let currentCategory = "All";
  let activeOrderId = null;
  let trackTimer = null;

  // -------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------
  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const setToken = (t) => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY);

  async function apiFetch(endpoint, options = {}) {
    const headers = options.headers || {};
    headers["Content-Type"] = "application/json";
    const token = getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    options.headers = headers;

    try {
      const res = await fetch(API_BASE + endpoint, options);
      if (res.status === 401 && !endpoint.includes("/api/auth/")) {
        // Token expired or invalid
        setToken(null);
        showAuthModal();
        throw new Error("Session expired. Please sign in again.");
      }
      return await res.json();
    } catch (err) {
      console.warn("API Error:", err);
      throw err;
    }
  }

  // -------------------------------------------------------------
  // Initialization
  // -------------------------------------------------------------
  async function init() {
    // Restore saved table preference
    const savedTable = localStorage.getItem(TABLE_KEY);
    if (savedTable) {
      const sel = document.getElementById("tableSelect");
      if (sel) sel.value = savedTable;
    }

    // Restore active order tracking if stored
    const savedOrderId = localStorage.getItem(ACTIVE_ORDER_KEY);
    if (savedOrderId) {
      activeOrderId = parseInt(savedOrderId);
    }

    // Verify authentication
    if (getToken()) {
      try {
        const res = await apiFetch("/api/auth/me");
        if (res && res.success) {
          currentUser = res.user;
          updateUserUI();
          hideAuthModal();
        } else {
          showAuthModal();
        }
      } catch (e) {
        showAuthModal();
      }
    } else {
      showAuthModal();
    }

    // Initial catalog load
    await loadMenu();
    if (currentUser) {
      await loadCart();
      if (activeOrderId) {
        startOrderTracking(activeOrderId);
      }
    }
  }

  function updateUserUI() {
    const greeting = document.getElementById("userGreeting");
    if (greeting) {
      greeting.textContent = currentUser ? `👤 ${currentUser.full_name}` : "Guest Diner";
    }
    const logoutBtn = document.getElementById("btnLogout");
    if (logoutBtn) {
      logoutBtn.style.display = currentUser ? "inline-block" : "none";
    }
  }

  function showAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) modal.style.display = "flex";
  }

  function hideAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) modal.style.display = "none";
  }

  function switchAuthTab(tab) {
    const tabLogin = document.getElementById("tabLogin");
    const tabRegister = document.getElementById("tabRegister");
    const formLogin = document.getElementById("formLogin");
    const formRegister = document.getElementById("formRegister");
    const errorBox = document.getElementById("authError");
    if (errorBox) errorBox.style.display = "none";

    if (tab === "login") {
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");
      formLogin.style.display = "block";
      formRegister.style.display = "none";
    } else {
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");
      formRegister.style.display = "block";
      formLogin.style.display = "none";
    }
  }

  // -------------------------------------------------------------
  // Authentication Actions (Independent Multi-Customer)
  // -------------------------------------------------------------
  async function handleLogin(e) {
    e.preventDefault();
    const errorBox = document.getElementById("authError");
    errorBox.style.display = "none";

    const u = document.getElementById("loginUsername").value.trim();
    const p = document.getElementById("loginPassword").value;

    try {
      const res = await apiFetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username: u, password: p })
      });

      if (res && res.success) {
        setToken(res.token);
        currentUser = res.user;
        updateUserUI();
        hideAuthModal();
        await loadCart();
        await loadMenu();
      } else {
        errorBox.textContent = res.error || "Login failed.";
        errorBox.style.display = "block";
      }
    } catch (err) {
      errorBox.textContent = err.message || "Network error. Please try again.";
      errorBox.style.display = "block";
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    const errorBox = document.getElementById("authError");
    errorBox.style.display = "none";

    const name = document.getElementById("regFullName").value.trim();
    const u = document.getElementById("regUsername").value.trim();
    const p = document.getElementById("regPassword").value;

    try {
      const res = await apiFetch("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ username: u, password: p, full_name: name })
      });

      if (res && res.success) {
        setToken(res.token);
        currentUser = res.user;
        updateUserUI();
        hideAuthModal();
        await loadCart();
        await loadMenu();
      } else {
        errorBox.textContent = res.error || "Registration failed.";
        errorBox.style.display = "block";
      }
    } catch (err) {
      errorBox.textContent = err.message || "Registration error.";
      errorBox.style.display = "block";
    }
  }

  async function logout() {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch (e) {}

    setToken(null);
    currentUser = null;
    if (trackTimer) {
      clearInterval(trackTimer);
      trackTimer = null;
    }
    updateUserUI();
    showAuthModal();
  }

  // -------------------------------------------------------------
  // Menu Catalog
  // -------------------------------------------------------------
  async function loadMenu() {
    try {
      const res = await apiFetch("/api/menu?available_only=false");
      if (res && res.success) {
        allMenuItems = res.items;
        renderCategoryPills(res.categories);
        renderMenuGrid();
      }
    } catch (e) {
      console.warn("Could not load menu:", e);
    }
  }

  function renderCategoryPills(categories) {
    const container = document.getElementById("categoryPills");
    if (!container) return;

    let html = `<button class="pill-btn ${currentCategory === 'All' ? 'active' : ''}" onclick="App.filterCategory('All')">All Items</button>`;
    categories.forEach(cat => {
      html += `<button class="pill-btn ${currentCategory === cat ? 'active' : ''}" onclick="App.filterCategory('${cat}')">${cat}</button>`;
    });
    container.innerHTML = html;
  }

  function filterCategory(cat) {
    currentCategory = cat;
    const pills = document.querySelectorAll(".pill-btn");
    pills.forEach(p => {
      if (p.textContent === cat || (cat === 'All' && p.textContent === 'All Items')) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });
    renderMenuGrid();
  }

  function onSearchInput() {
    renderMenuGrid();
  }

  function renderMenuGrid() {
    const container = document.getElementById("menuGrid");
    if (!container) return;

    const query = (document.getElementById("menuSearch")?.value || "").toLowerCase().trim();

    const filtered = allMenuItems.filter(it => {
      const matchCat = (currentCategory === "All" || it.category === currentCategory);
      const matchQuery = !query || it.name.toLowerCase().includes(query) || it.category.toLowerCase().includes(query);
      return matchCat && matchQuery;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div class="loader-box">No gourmet dishes found matching "${query}".</div>`;
      return;
    }

    let html = "";
    filtered.forEach(it => {
      html += `
        <div class="dish-card">
          <div>
            <div class="dish-header">
              <div class="dish-name">${it.name}</div>
            </div>
            <div class="dish-cat">${it.category}</div>
          </div>
          <div class="dish-footer">
            <span class="dish-price">₹${parseFloat(it.price).toFixed(2)}</span>
            <button class="btn-add-dish" ${it.is_available ? '' : 'disabled'} onclick="App.addToCart(${it.id})">
              ${it.is_available ? '+ Add to Cart' : 'Out of Stock'}
            </button>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  // -------------------------------------------------------------
  // Cart Management (Isolated per customer token)
  // -------------------------------------------------------------
  async function loadCart() {
    if (!getToken()) return;
    try {
      const res = await apiFetch("/api/cart");
      if (res && res.success) {
        renderCartUI(res.cart);
      }
    } catch (e) {}
  }

  async function addToCart(menuItemId) {
    if (!currentUser) {
      showAuthModal();
      return;
    }

    try {
      const res = await apiFetch("/api/cart/add", {
        method: "POST",
        body: JSON.stringify({ menu_item_id: menuItemId, quantity: 1 })
      });
      if (res && res.success) {
        renderCartUI(res.cart);
      }
    } catch (e) {
      alert("Could not add dish: " + e.message);
    }
  }

  async function updateCartQty(menuItemId, newQty) {
    try {
      const res = await apiFetch("/api/cart/update", {
        method: "POST",
        body: JSON.stringify({ menu_item_id: menuItemId, quantity: newQty })
      });
      if (res && res.success) {
        renderCartUI(res.cart);
      }
    } catch (e) {}
  }

  function renderCartUI(cart) {
    const badge = document.getElementById("cartCount");
    const totalText = document.getElementById("cartTotalText");
    const container = document.getElementById("cartItemsContainer");
    const subtotalText = document.getElementById("billSubtotal");
    const taxText = document.getElementById("billTax");
    const grandTotalText = document.getElementById("billGrandTotal");

    if (badge) badge.textContent = cart.item_count;
    if (totalText) totalText.textContent = `₹${parseFloat(cart.net_total).toFixed(2)}`;
    if (subtotalText) subtotalText.textContent = `₹${parseFloat(cart.subtotal).toFixed(2)}`;
    if (taxText) taxText.textContent = `₹${parseFloat(cart.tax_amount).toFixed(2)}`;
    if (grandTotalText) grandTotalText.textContent = `₹${parseFloat(cart.net_total).toFixed(2)}`;

    if (!container) return;

    if (cart.is_empty) {
      container.innerHTML = `<div class="empty-cart-msg">Your cart is currently empty.<br>Browse our menu and add dishes to order.</div>`;
      return;
    }

    let html = "";
    cart.items.forEach(it => {
      html += `
        <div class="cart-item-row">
          <div class="cart-item-left">
            <h4>${it.item_name}</h4>
            <p>₹${parseFloat(it.unit_price).toFixed(2)} each</p>
          </div>
          <div class="cart-qty-ctrls">
            <button class="btn-qty" onclick="App.updateCartQty(${it.menu_item_id}, ${it.quantity - 1})">-</button>
            <span class="qty-val">${it.quantity}</span>
            <button class="btn-qty" onclick="App.updateCartQty(${it.menu_item_id}, ${it.quantity + 1})">+</button>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  function toggleCartDrawer() {
    const drawer = document.getElementById("cartDrawer");
    const overlay = document.getElementById("cartOverlay");
    if (drawer && overlay) {
      drawer.classList.toggle("open");
      overlay.classList.toggle("open");
    }
  }

  // -------------------------------------------------------------
  // Order Placement (Checkout)
  // -------------------------------------------------------------
  async function placeOrder() {
    const tableSelect = document.getElementById("tableSelect");
    const tableNum = tableSelect ? tableSelect.value : "Table 1";
    const notesInput = document.getElementById("orderNotes");
    const notes = notesInput ? notesInput.value.trim() : "";

    const btn = document.getElementById("btnPlaceOrder");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Disptaching to Kitchen...";
    }

    try {
      const res = await apiFetch("/api/orders/checkout", {
        method: "POST",
        body: JSON.stringify({
          table_number: tableNum,
          special_instructions: notes
        })
      });

      if (res && res.success) {
        toggleCartDrawer();
        activeOrderId = res.order.id;
        localStorage.setItem(ACTIVE_ORDER_KEY, activeOrderId.toString());

        // Switch to Tracker View immediately
        switchView("viewTrack");
        startOrderTracking(activeOrderId);
      } else {
        alert(res.error || "Order placement failed.");
      }
    } catch (e) {
      alert("Order error: " + e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "🚀 Disptach Order to Kitchen";
      }
    }
  }

  // -------------------------------------------------------------
  // Live Real-Time Order Tracking (3-Second Auto-Poll)
  // -------------------------------------------------------------
  function startOrderTracking(orderId) {
    if (trackTimer) clearInterval(trackTimer);
    pollOrderStatus(orderId);
    trackTimer = setInterval(() => pollOrderStatus(orderId), 3000);
  }

  async function pollOrderStatus(orderId) {
    if (!orderId) return;
    try {
      const res = await apiFetch(`/api/orders/${orderId}/track`);
      if (res && res.success) {
        renderTracker(res);
      }
    } catch (e) {}
  }

  function renderTracker(data) {
    const title = document.getElementById("trackOrderNum");
    const meta = document.getElementById("trackOrderMeta");
    const badge = document.getElementById("trackMainBadge");
    const headline = document.getElementById("trackHeadline");
    const lifeKitchen = document.getElementById("lifeKitchen");
    const lifeServing = document.getElementById("lifeServing");
    const lifeBilling = document.getElementById("lifeBilling");
    const lifePayment = document.getElementById("lifePayment");
    const itemsList = document.getElementById("trackItemsList");
    const totalEl = document.getElementById("trackTotal");

    if (title) title.textContent = `Order #${data.order_number}`;
    if (meta) meta.textContent = `Table: ${data.table_number} | Placed: ${data.created_at || 'Just now'} | Server: ${data.waiter}`;
    if (headline) headline.textContent = data.headline;
    if (badge) {
      badge.textContent = data.lifecycle.serving_status === "SERVED" ? "SERVED" : (data.lifecycle.kitchen_status === "READY" ? "READY" : data.lifecycle.kitchen_status);
      badge.style.backgroundColor = data.lifecycle.billing_status === "SETTLED" ? "var(--success)" : "var(--accent)";
    }

    if (lifeKitchen) lifeKitchen.textContent = data.lifecycle.kitchen_status;
    if (lifeServing) lifeServing.textContent = data.lifecycle.serving_status;
    if (lifeBilling) lifeBilling.textContent = data.lifecycle.billing_status;
    if (lifePayment) lifePayment.textContent = data.lifecycle.payment_status;

    if (totalEl) totalEl.textContent = `₹${parseFloat(data.bill ? data.bill.final_total : data.subtotal).toFixed(2)}`;

    // Update 5-step stepper visually
    const step = data.overall_step;
    for (let i = 1; i <= 5; i++) {
      const stepEl = document.getElementById(`step${i}`);
      const lineEl = document.getElementById(`line${i}`);
      if (stepEl) {
        if (i < step) {
          stepEl.className = "step-item completed";
        } else if (i === Math.floor(step)) {
          stepEl.className = "step-item active";
        } else {
          stepEl.className = "step-item";
        }
      }
      if (lineEl) {
        if (i < step) {
          lineEl.className = "step-line active";
        } else {
          lineEl.className = "step-line";
        }
      }
    }

    // Render item summary list
    if (itemsList && data.items) {
      let html = "";
      data.items.forEach(it => {
        html += `
          <div style="display:flex; justify-content:space-between; font-size:12px; padding:4px 0;">
            <span>${it.name} ×${it.quantity}</span>
            <span>₹${parseFloat(it.line_total).toFixed(2)}</span>
          </div>
        `;
      });
      itemsList.innerHTML = html;
    }
  }

  // -------------------------------------------------------------
  // View Switching
  // -------------------------------------------------------------
  function switchView(viewId) {
    const views = ["viewMenu", "viewTrack", "viewHistory"];
    views.forEach(v => {
      const el = document.getElementById(v);
      if (el) el.classList.toggle("active", v === viewId);
    });

    const navItems = {
      viewMenu: "navMenu",
      viewTrack: "navTrack",
      viewHistory: "navHistory"
    };

    Object.keys(navItems).forEach(vKey => {
      const navEl = document.getElementById(navItems[vKey]);
      if (navEl) navEl.classList.toggle("active", vKey === viewId);
    });

    if (viewId === "viewHistory") {
      loadHistory();
    }
    if (viewId === "viewTrack" && activeOrderId) {
      pollOrderStatus(activeOrderId);
    }
  }

  async function loadHistory() {
    const container = document.getElementById("historyList");
    if (!container) return;

    try {
      const res = await apiFetch("/api/orders");
      if (res && res.success) {
        if (res.orders.length === 0) {
          container.innerHTML = `<div class="loader-box">You have not placed any orders yet.</div>`;
          return;
        }

        let html = "";
        res.orders.forEach(o => {
          html += `
            <div class="history-card">
              <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="font-weight:700; font-family:Consolas;">#${o.order_number}</span>
                <span class="status-badge" style="font-size:10px;">${o.status}</span>
              </div>
              <div style="font-size:11px; color:var(--text-muted); margin-bottom:6px;">
                Table: ${o.table_number} | ${o.created_at}
              </div>
              <div style="font-size:12px; margin-bottom:8px;">
                ${o.items_summary}
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="price-hl">₹${parseFloat(o.subtotal).toFixed(2)}</span>
                <button class="btn-secondary" style="padding:5px 10px; font-size:11px;" onclick="App.trackPastOrder(${o.id})">Track Status</button>
              </div>
            </div>
          `;
        });
        container.innerHTML = html;
      }
    } catch (e) {
      container.innerHTML = `<div class="loader-box">Could not load history.</div>`;
    }
  }

  function trackPastOrder(id) {
    activeOrderId = id;
    localStorage.setItem(ACTIVE_ORDER_KEY, id.toString());
    switchView("viewTrack");
    startOrderTracking(id);
  }

  function onTableChange() {
    const sel = document.getElementById("tableSelect");
    if (sel) {
      localStorage.setItem(TABLE_KEY, sel.value);
    }
  }

  // -------------------------------------------------------------
  // Floor Service & Feedback Modals
  // -------------------------------------------------------------
  function openServiceModal() {
    const m = document.getElementById("serviceModal");
    if (m) m.style.display = "flex";
  }

  function closeServiceModal() {
    const m = document.getElementById("serviceModal");
    if (m) m.style.display = "none";
  }

  async function submitServiceRequest(reqType) {
    const tableSelect = document.getElementById("tableSelect");
    const tableNum = tableSelect ? tableSelect.value : "Table 1";

    try {
      const res = await apiFetch("/api/service-requests", {
        method: "POST",
        body: JSON.stringify({
          table_number: tableNum,
          request_type: reqType,
          order_id: activeOrderId
        })
      });
      closeServiceModal();
      alert(`✅ Floor waiter summoned for ${reqType} at ${tableNum}.`);
    } catch (e) {
      alert("Error calling server: " + e.message);
    }
  }

  function openFeedbackModal() {
    const m = document.getElementById("feedbackModal");
    if (m) m.style.display = "flex";
  }

  function closeFeedbackModal() {
    const m = document.getElementById("feedbackModal");
    if (m) m.style.display = "none";
  }

  async function submitFeedback(e) {
    e.preventDefault();
    const rating = parseInt(document.getElementById("fbRating").value);
    const comments = document.getElementById("fbComments").value;

    try {
      const res = await apiFetch("/api/feedback", {
        method: "POST",
        body: JSON.stringify({
          order_id: activeOrderId,
          rating: rating,
          comments: comments
        })
      });
      closeFeedbackModal();
      alert("✅ Thank you! Your review has been recorded.");
    } catch (e) {
      alert("Error submitting review: " + e.message);
    }
  }

  // Public Interface
  return {
    init,
    login: handleLogin,
    register: handleRegister,
    logout,
    switchAuthTab,
    handleLogin,
    handleRegister,
    filterCategory,
    onSearchInput,
    addToCart,
    updateCartQty,
    toggleCartDrawer,
    placeOrder,
    switchView,
    trackPastOrder,
    onTableChange,
    openServiceModal,
    closeServiceModal,
    submitServiceRequest,
    openFeedbackModal,
    closeFeedbackModal,
    submitFeedback
  };
})();

// Bootstrap on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
