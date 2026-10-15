import { useCallback, useEffect, useMemo, useRef, useState } from "react";

/* ========================================================================
 * CONFIG
 * ===================================================================== */

const API_DEFAULT = "http://localhost:8000";

const BUSINESS_TYPE_GROUPS = [
  {
    label: "Retail and everyday trade",
    options: [
      "Kiosk / kibanda / informal shop",
      "Duka / general shop",
      "Convenience shop",
      "Mini-market / supermarket",
      "Hypermarket / department store",
      "Wholesale shop / cash-and-carry",
      "Distributors / importers / exporters",
      "Clothing, shoes and fashion",
      "Beauty, cosmetics and personal care",
      "Electronics, phones and accessories",
      "Furniture, homeware and appliances",
      "Hardware, building materials and plumbing",
      "Auto parts, tyres and vehicle accessories",
      "Pharmacy / chemist / medical supplies",
      "Books, stationery, printing and office supplies",
      "Bags, jewellery, gifts and crafts",
      "Pet supplies and agricultural inputs",
      "Second-hand / mitumba / resale",
      "Online store / e-commerce",
      "Market trader / stall / market vendor",
      "Other retail or wholesale",
    ],
  },
  {
    label: "Food, farming and natural resources",
    options: [
      "Grocery, greengrocer and fresh produce",
      "Butchery, fishmonger and poultry shop",
      "Bakery, cakes and confectionery",
      "Restaurant, hotel dining and catering",
      "Café, tea, coffee and juice shop",
      "Bar, pub and beverage outlet",
      "Food truck, takeaway and street food",
      "Food and beverage manufacturing / processing",
      "Farm, ranch, dairy and livestock",
      "Crop farming, horticulture and floriculture",
      "Fisheries and aquaculture",
      "Agricultural cooperative / produce aggregator",
      "Agrovet, seeds, fertiliser and farm machinery",
      "Forestry, timber and wood products",
      "Mining, quarrying, minerals and related services",
      "Water, sanitation and waste management",
    ],
  },
  {
    label: "Manufacturing and construction",
    options: [
      "Manufacturing / factory",
      "Textiles, garments and leather production",
      "Furniture, carpentry and woodwork",
      "Metal fabrication and engineering",
      "Packaging, paper and printing production",
      "Chemicals, plastics and household products",
      "Building contractor / civil engineering",
      "Construction trades and specialist installation",
      "Architecture, surveying and quantity surveying",
      "Property development and real estate",
      "Property rental, facilities and property management",
      "Energy, solar and electrical services",
    ],
  },
  {
    label: "Transport, hospitality and travel",
    options: [
      "Matatu, bus and passenger transport",
      "Taxi, ride-hailing and car hire",
      "Courier, parcel and delivery service",
      "Trucking, freight and logistics",
      "Warehouse, cold storage and fulfilment",
      "Travel agency, tour operator and safari",
      "Hotel, lodge, guest house and accommodation",
      "Events, venues and entertainment",
      "Vehicle sales, servicing and repair",
      "Fuel station and energy retail",
    ],
  },
  {
    label: "Health, education and personal services",
    options: [
      "Hospital, clinic and medical practice",
      "Dental, optical and specialist health practice",
      "Laboratory, diagnostics and health technology",
      "Veterinary practice and animal care",
      "School, college, university and training centre",
      "Childcare, early learning and tutoring",
      "Salon, barber, spa and wellness",
      "Gym, sports, fitness and recreation",
      "Laundry, dry cleaning and cleaning services",
      "Funeral services and related retail",
      "Repair, maintenance and household services",
      "Security and guarding services",
    ],
  },
  {
    label: "Professional, financial and digital services",
    options: [
      "Professional services / consultancy",
      "Accounting, bookkeeping and tax services",
      "Legal practice and company secretarial services",
      "Bank, microfinance, SACCO and credit provider",
      "Insurance and brokerage",
      "Mobile money agent and payments business",
      "Technology, software and IT services",
      "Telecommunications and internet services",
      "Digital marketing, advertising and media",
      "Photography, design and creative studio",
      "Recruitment, staffing and human resources",
      "NGO, nonprofit, community organisation or social enterprise",
      "Government, county or public-sector organisation",
      "Holding company / enterprise group",
    ],
  },
];

const ENDPOINTS = {
  login: "/api/v1/auth/login/",
  signup: "/api/v1/auth/signup/",
  logout: "/api/v1/auth/logout/",
  refresh: "/api/v1/auth/refresh/",

  products: "/api/v1/inventory/products/",
  categories: "/api/v1/inventory/categories/",
  stockMovements: "/api/v1/inventory/stock/adjust/",

  tills: "/api/v1/sales/tills/",
  tillOpen: "/api/v1/sales/tills/open/",
  tillCurrent: "/api/v1/sales/tills/current/",
  tillClose: "/api/v1/sales/tills/close/",
  tillHistory: "/api/v1/sales/tills/history/",

  sales: "/api/v1/sales/",
  customers: "/api/v1/sales/customers/",

  purchases: "/api/v1/purchasing/orders/",
  suppliers: "/api/v1/purchasing/suppliers/",
  purchaseReceive: "/api/v1/purchasing/receive/",
  mpesa: "/api/v1/payments/mpesa/initiate/",

  reports: "/api/v1/reports/dashboard/",
  salesReport: "/api/v1/reports/sales/",
  notifications: "/api/v1/notifications/",
  notificationsRead: "/api/v1/notifications/read/",
  audit: "/api/v1/audit/",
  users: "/api/v1/users/",
};

const NAV = [
  { key: "dashboard", label: "Dashboard" },
  { key: "pos", label: "Point of Sale" },
  { key: "sales", label: "Sales" },
  { key: "inventory", label: "Inventory" },
  { key: "purchasing", label: "Purchasing" },
  { key: "reports", label: "Reports" },
  { key: "customers", label: "Customers" },
  { key: "notifications", label: "Notifications" },
  { key: "audit", label: "Audit" },
  { key: "users", label: "Users" },
];

/* ========================================================================
 * Helpers
 * ===================================================================== */

const STORAGE_KEY = "pos_tokens";

function loadTokens() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
function saveTokens(t) {
  try {
    if (t && t.access) localStorage.setItem(STORAGE_KEY, JSON.stringify(t));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {}
}
function title(s = "") {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
function joinUrl(base, path) {
  const b = (base || "").replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${b}${p}`;
}
function money(n) {
  const v = Number(n || 0);
  return v.toLocaleString("en-KE", {
    style: "currency",
    currency: "KES",
    minimumFractionDigits: 2,
  });
}
function uuid() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function tokenExpired(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(payload.padEnd(payload.length + (4 - payload.length % 4) % 4, "=")));
    return !decoded.exp || decoded.exp <= Math.floor(Date.now() / 1000) + 30;
  } catch {
    return true;
  }
}
function listOf(data) {
  if (Array.isArray(data)) return data;
  return data?.results || [];
}
/* Read stock from whichever field the backend used. */
function getStock(p) {
  if (p == null) return 0;
  if (p.stock_quantity !== undefined) return Number(p.stock_quantity);
  if (p.stock !== undefined) return Number(p.stock);
  if (p.quantity_on_hand !== undefined) return Number(p.quantity_on_hand);
  return 0;
}
function getPrice(p) {
  if (p == null) return 0;
  return Number(p.price ?? p.sale_price ?? p.selling_price ?? p.unit_price ?? 0);
}
function getReorder(p) {
  return Number(p?.reorder_level ?? p?.reorder_point ?? p?.low_stock_threshold ?? 0);
}

/* ========================================================================
 * App
 * ===================================================================== */

export default function App() {
  const api = API_DEFAULT;
  const [tokens, setTokens] = useState(loadTokens);
  const [view, setView] = useState("dashboard");
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [till, setTill] = useState(null);
  const [tillLoaded, setTillLoaded] = useState(false);

  const auth = Boolean(tokens?.access);

  const notify = useCallback((kind, text) => {
    setToast({ kind, text, at: Date.now() });
    window.clearTimeout(notify._t);
    notify._t = window.setTimeout(() => setToast(null), 4000);
  }, []);

  const refreshPromise = useRef(null);
  const refreshAccess = useCallback(async () => {
    if (!tokens?.refresh) return null;
    if (refreshPromise.current) return refreshPromise.current;
    refreshPromise.current = (async () => {
      try {
        const res = await fetch(joinUrl(api, ENDPOINTS.refresh), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: tokens.refresh }),
        });
        if (!res.ok) throw new Error("refresh failed");
        const data = await res.json();
        const merged = { ...tokens, ...data };
        setTokens(merged);
        saveTokens(merged);
        return merged.access;
      } catch {
        setTokens({});
        saveTokens({});
        return null;
      } finally {
        refreshPromise.current = null;
      }
    })();
    return refreshPromise.current;
  }, [api, tokens]);

  const apiFetch = useCallback(
    async (path, { method = "GET", body, auth: needAuth = true, retry = true } = {}) => {
      const headers = { Accept: "application/json" };
      if (body !== undefined) headers["Content-Type"] = "application/json";
      const t = tokens?.access ? tokens : loadTokens();
      let access = t?.access;
      if (needAuth && retry && t?.refresh && (!access || tokenExpired(access))) {
        access = await refreshAccess();
        if (!access) throw new Error("Your session expired. Please sign in again.");
      }
      if (needAuth && !access) throw new Error("Your session is not authenticated. Please sign in again.");
      if (needAuth && access) headers.Authorization = `Bearer ${access}`;

      const res = await fetch(joinUrl(api, path), {
        method,
        headers,
        credentials: "omit",
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });

      if (res.status === 401 && needAuth && retry && t?.refresh) {
        const newAccess = await refreshAccess();
        if (newAccess) return apiFetch(path, { method, body, auth: needAuth, retry: false });
      }

      const text = await res.text();
      const isJson = (res.headers.get("content-type") || "").includes("application/json");
      let data = text;
      if (isJson && text) {
        try { data = JSON.parse(text); } catch { data = text; }
      }

      if (!res.ok) {
        const err = new Error(pickErrorMessage(data, res.status));
        err.status = res.status;
        err.data = data;
        throw err;
      }
      if (res.status === 204) return null;
      return data;
    },
    [api, refreshAccess, tokens]
  );

  useEffect(() => {
    if (!auth) { setTill(null); setTillLoaded(true); return; }
    let cancelled = false;
    setTillLoaded(false);
    (async () => {
      try {
        const data = await apiFetch(ENDPOINTS.tillCurrent);
        if (!cancelled) setTill(data && data.id ? data : null);
      } catch {
        if (!cancelled) setTill(null);
      } finally {
        if (!cancelled) setTillLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [auth, apiFetch]);

  const handleAuth = async (payload) => {
    setBusy(true);
    try {
      const path = mode === "login" ? ENDPOINTS.login : ENDPOINTS.signup;
      const data = await apiFetch(path, { method: "POST", body: payload, auth: false });
      if (mode === "login" && data?.access) {
        setTokens(data);
        saveTokens(data);
        notify("ok", "Signed in.");
        setView("dashboard");
        return;
      }
      if (mode === "signup") {
        notify("ok", "Account created. Please sign in.");
        setMode("login");
      }
    } catch (e) {
      notify("err", e.message || "Authentication failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    try {
      if (tokens?.refresh) {
        await apiFetch(ENDPOINTS.logout, { method: "POST", body: { refresh: tokens.refresh } });
      }
    } catch {}
    setTokens({});
    saveTokens({});
    setTill(null);
    setView("dashboard");
    notify("ok", "Signed out.");
  };

  if (!auth) {
    return (
      <main className="app">
        <style>{css}</style>
        {toast && <Toast toast={toast} />}
        <div className="auth-shell">
          <div className="auth-card card">
            <div className="brand-center">
              <span className="eyebrow">TENANT POS</span>
              <h1>Store Operations</h1>
              <p>Sign in to open your till.</p>
            </div>
            <AuthForm
              mode={mode}
              setMode={setMode}
              busy={busy}
              onSubmit={handleAuth}
            />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="app">
      <style>{css}</style>
      {toast && <Toast toast={toast} />}

      <Topbar till={till} tokens={tokens} onLogout={handleLogout} />

      <div className="layout">
        {till && <Sidebar items={NAV} active={view} onSelect={setView} till={till} />}

        <section className={`content ${!till ? "till-setup-content" : ""}`}>
          {!tillLoaded ? (
            <section className="card center-card"><p className="muted">Checking till session…</p></section>
          ) : !till ? (
            <>
              <OpenTill
                apiFetch={apiFetch}
                onOpened={(t) => { setTill(t); setView("dashboard"); notify("ok", "Till opened."); }}
                busy={busy}
                setBusy={setBusy}
                notify={notify}
              />
              <TillHistory apiFetch={apiFetch} />
            </>
          ) : (
            <>
              {view === "dashboard" && (
                <Dashboard
                  apiFetch={apiFetch}
                  till={till}
                  onNavigate={setView}
                  notify={notify}
                  onTillClosed={() => setTill(null)}
                />
              )}
              {view === "pos" && (
                <POS apiFetch={apiFetch} till={till} notify={notify} onCompleted={() => notify("ok", "Sale completed.")} />
              )}
              {view === "sales" && <SalesList apiFetch={apiFetch} notify={notify} />}
              {view === "inventory" && <InventoryPage apiFetch={apiFetch} notify={notify} />}
              {view === "purchasing" && (
                <PurchasingPage apiFetch={apiFetch} notify={notify} />
              )}
              {view === "reports" && <Reports apiFetch={apiFetch} notify={notify} />}
              {view === "customers" && (
                <CustomersPage apiFetch={apiFetch} notify={notify} />
              )}
              {view === "notifications" && (
                <NotificationsPage apiFetch={apiFetch} notify={notify} />
              )}
              {view === "audit" && (
                <AuditPage apiFetch={apiFetch} />
              )}
              {view === "users" && (
                <SimpleList title="Users" endpoint={ENDPOINTS.users} apiFetch={apiFetch} notify={notify} />
              )}

            </>
          )}
        </section>
      </div>
    </main>
  );
}

/* ========================================================================
 * Error helpers
 * ===================================================================== */

function pickErrorMessage(data, status) {
  if (!data) return `Request failed (${status})`;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  if (data.message) return data.message;
  if (data.error) return typeof data.error === "string" ? data.error : JSON.stringify(data.error);
  /* DRF field errors: {"field": ["msg"]} */
  const parts = [];
  for (const [k, v] of Object.entries(data)) {
    const text = Array.isArray(v) ? v.join(" ") : String(v);
    parts.push(`${k}: ${text}`);
  }
  return parts.length ? parts.join(" • ") : `Request failed (${status})`;
}

/* ========================================================================
 * UI shell
 * ===================================================================== */

function Toast({ toast }) {
  return <div className={`toast toast-${toast.kind}`} role="status">{toast.text}</div>;
}

function Topbar({ till, tokens, onLogout }) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="eyebrow">TENANT POS</span>
        <h1>Store Operations</h1>
        <p>{tokens?.tenant_schema ? `Tenant: ${tokens.tenant_schema}` : "Connected to Django."}</p>
      </div>
      <div className="topbar-right">
        {till && (
          <div className="till-badge">
            <span className="till-dot" />
            <div>
              <strong>Till #{till.terminal_id || "terminal"}</strong>
              <span>Session #{till.id}</span>
            </div>
          </div>
        )}
        <button className="ghost" onClick={onLogout}>Sign out</button>
      </div>
    </header>
  );
}

function Sidebar({ items, active, onSelect, till }) {
  return (
    <aside className="sidebar">
      <nav className="navigation">
        {items.map((it) => (
          <button key={it.key} className={`nav ${active === it.key ? "active" : ""}`} onClick={() => onSelect(it.key)}>
            <span>{it.label}</span>
          </button>
        ))}
      </nav>
      {till && (
        <div className="sidebar-foot">
          <span className="eyebrow">Cashier session</span>
          <strong>Till #{till.terminal_id || "terminal"}</strong>
          <span className="muted-small">
            Session #{till.id} · Opened {new Date(till.opened_at || Date.now()).toLocaleString()}
          </span>
        </div>
      )}
    </aside>
  );
}

/* ========================================================================
 * Modal
 * ===================================================================== */

function Modal({ open, title: heading, onClose, children, wide }) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className={`modal ${wide ? "wide" : ""}`} onClick={(e) => e.stopPropagation()}>
        <header className="modal-head">
          <h3>{heading}</h3>
          <button className="ghost small" onClick={onClose}>Close</button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

/* ========================================================================
 * Auth
 * ===================================================================== */

function AuthForm({ mode, setMode, busy, onSubmit }) {
  const [form, setForm] = useState({
    business_name: "",
    business_type: "",
    business_type_other: "",
    username: "",
    password: "",
  });
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const isLogin = mode === "login";

  const submit = (e) => {
    e.preventDefault();
    const payload = isLogin
      ? { username: form.username, password: form.password }
      : {
          business_name: form.business_name,
          business_type: form.business_type === "Other / not listed"
            ? form.business_type_other.trim()
            : form.business_type,
          username: form.username,
          password: form.password,
        };
    onSubmit(payload);
  };

  return (
    <form onSubmit={submit} className="auth-form">
      {!isLogin && (
        <>
          <Field label="Business name" value={form.business_name} onChange={set("business_name")} required />
          <label className="field">
            <span>Business type</span>
            <select value={form.business_type} onChange={set("business_type")} required>
              <option value="">Select the closest match</option>
              {BUSINESS_TYPE_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map((option) => <option key={option} value={option}>{option}</option>)}
                </optgroup>
              ))}
              <option value="Other / not listed">Other / not listed</option>
            </select>
          </label>
          {form.business_type === "Other / not listed" && (
            <Field
              label="Describe your business type"
              value={form.business_type_other}
              onChange={set("business_type_other")}
              required
            />
          )}
        </>
      )}
      <Field label="Username" value={form.username} onChange={set("username")} required autoComplete="username" />
      <Field
        label="Password"
        type="password"
        value={form.password}
        onChange={set("password")}
        required
        minLength={isLogin ? undefined : 8}
        autoComplete={isLogin ? "current-password" : "new-password"}
      />
      <button className="primary wide" disabled={busy}>
        {busy ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
      </button>

      <button type="button" className="link-button" onClick={() => setMode(isLogin ? "signup" : "login")}>
        {isLogin ? "New store? Create one" : "Already registered? Sign in"}
      </button>
    </form>
  );
}

/* ========================================================================
 * Open / close till
 * ===================================================================== */

function OpenTill({ apiFetch, onOpened, busy, setBusy, notify }) {
  const [form, setForm] = useState({ terminal_id: "TILL-01", opening_float: "0" });
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const data = await apiFetch(ENDPOINTS.tillOpen, {
        method: "POST",
        body: { terminal_id: form.terminal_id, float_amount: Number(form.opening_float || 0) },
      });
      onOpened(data);
    } catch (err) {
      notify("err", err.message || "Could not open till.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card center-card">
      <span className="eyebrow">CASHIER</span>
      <h2>Open a till to start selling</h2>
      <p className="muted">
        A till session is required before creating sales. Use a stable till number (for example, TILL-01) for this checkout; each opening creates a separate session.
      </p>
      <form onSubmit={submit} className="form-tight">
        <Field label="Till number / terminal ID" value={form.terminal_id} onChange={set("terminal_id")} required />
        <Field
          label="Opening float (KES)"
          type="number"
          step="0.01"
          min="0"
          value={form.opening_float}
          onChange={set("opening_float")}
        />
        <button className="primary wide" disabled={busy}>{busy ? "Opening…" : "Open till"}</button>
      </form>
    </section>
  );
}

function CloseTillBar({ till, apiFetch, notify, onClosed }) {
  const [counted, setCounted] = useState("");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const close = async () => {
    setBusy(true);
    try {
      await apiFetch(ENDPOINTS.tillClose, {
        method: "POST",
        body: { session_id: till.id, counted_cash: Number(counted || 0) },
      });
      notify("ok", "Till closed.");
      onClosed();
    } catch (e) {
      notify("err", e.message || "Could not close till.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="till-bar">
      {!open ? (
        <button className="ghost" onClick={() => setOpen(true)}>Close till…</button>
      ) : (
        <div className="till-bar-row">
          <span>Counted cash (KES)</span>
          <input type="number" step="0.01" min="0" value={counted} onChange={(e) => setCounted(e.target.value)} placeholder="0.00" />
          <button className="primary" disabled={busy} onClick={close}>{busy ? "Closing…" : "Confirm close"}</button>
          <button className="ghost" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
}

/* ========================================================================
 * Dashboard
 * ===================================================================== */

function Dashboard({ apiFetch, till, onNavigate, notify, onTillClosed }) {
  const [metrics, setMetrics] = useState(null);
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const data = await apiFetch(ENDPOINTS.reports);
        if (!cancel) setMetrics(data);
      } catch {}
    })();
    return () => { cancel = true; };
  }, [apiFetch]);

  const cards = [
    { k: "today_revenue", label: "Today's revenue" },
    { k: "today_sales", label: "Sales today" },
    { k: "low_stock_count", label: "Low stock items" },
    { k: "pending_orders", label: "Pending orders" },
  ];

  return (
    <>
      <section className="card">
        <div className="section-intro">
          <span className="eyebrow">OVERVIEW</span>
          <h2>Dashboard</h2>
          <p>{till ? `Till #${till.terminal_id || "terminal"} is open.` : "Open a till to begin selling."}</p>
        </div>
        <div className="stat-grid">
          {cards.map((c) => (
            <div key={c.k} className="stat">
              <span className="eyebrow">{c.label}</span>
              <strong>{metrics && metrics[c.k] !== undefined ? metrics[c.k] : "—"}</strong>
            </div>
          ))}
        </div>
        <div className="quick-actions">
          <button className="primary" onClick={() => onNavigate("pos")}>Open POS</button>
          <button className="secondary" onClick={() => onNavigate("inventory")}>Inventory</button>
          <button className="secondary" onClick={() => onNavigate("sales")}>Sales</button>
        </div>
      </section>
      <CloseTillBar till={till} apiFetch={apiFetch} notify={notify} onClosed={onTillClosed} />
      <TillHistory apiFetch={apiFetch} />
    </>
  );
}

function TillHistory({ apiFetch }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch(ENDPOINTS.tillHistory);
      setRows(listOf(data));
    } catch (e) {
      setError(e.message || "Could not load till history.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);

  useEffect(() => { load(); }, [load]);

  const date = (value) => value ? new Date(value).toLocaleString() : "—";
  const columns = [
    { key: "terminal_id", label: "Till" },
    { key: "status", label: "Status", render: (row) => title(row.status) },
    { key: "opened_at", label: "Opened", render: (row) => date(row.opened_at) },
    { key: "opened_by", label: "Opened by" },
    { key: "opening_float", label: "Opening float", render: (row) => money(row.opening_float) },
    { key: "closed_at", label: "Closed", render: (row) => date(row.closed_at) },
    { key: "closed_by", label: "Closed by" },
    { key: "sales_count", label: "Sales" },
    { key: "cash_sales_total", label: "Cash sales", render: (row) => money(row.cash_sales_total) },
    { key: "counted_cash", label: "Counted cash", render: (row) => row.counted_cash == null ? "—" : money(row.counted_cash) },
    { key: "expected_cash", label: "Expected cash", render: (row) => money(row.expected_cash) },
    { key: "variance", label: "Variance", render: (row) => row.variance == null ? "—" : money(row.variance) },
  ];

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro">
          <span className="eyebrow">CASHIER</span>
          <h2>Till session history</h2>
          <p>Opening and closing records are retained for reconciliation.</p>
        </div>
        <div className="list-tools">
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        </div>
      </div>
      {error ? <p className="form-error">{error}</p> : loading ? <p className="muted">Loading session history…</p> : !rows.length ? <p className="muted">No till sessions recorded yet.</p> : <Table columns={columns} rows={rows} />}
    </section>
  );
}

/* ========================================================================
 * POS
 * ===================================================================== */

function POS({ apiFetch, till, notify, onCompleted }) {
  const [products, setProducts] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [cart, setCart] = useState([]);
  const [customer, setCustomer] = useState("");
  const [payMethod, setPayMethod] = useState("cash");
  const [cashGiven, setCashGiven] = useState("");
  const [mpesaPhone, setMpesaPhone] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [lastReceipt, setLastReceipt] = useState(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      setLoading(true);
      try {
        const data = await apiFetch(ENDPOINTS.products);
        if (!cancel) setProducts(listOf(data));
      } catch (e) {
        notify("err", e.message || "Could not load products.");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => { cancel = true; };
  }, [apiFetch, notify]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return products.filter((p) => {
      const name = (p.name || "").toLowerCase();
      const sku = (p.sku || "").toString().toLowerCase();
      const barcode = (p.barcode || "").toString().toLowerCase();
      return name.includes(q) || sku.includes(q) || barcode.includes(q);
    }).slice(0, 40);
  }, [products, query]);

  const addToCart = (p) => {
    setCart((c) => {
      const i = c.findIndex((l) => l.product === p.id);
      if (i >= 0) {
        const copy = [...c];
        copy[i] = { ...copy[i], quantity: copy[i].quantity + 1 };
        return copy;
      }
      return [
        ...c,
        {
          product: p.id,
          name: p.name,
          sku: p.sku || p.barcode || "",
          unit_price: getPrice(p),
          tax_rate: Number(p.tax_rate ?? 0),
          quantity: 1,
        },
      ];
    });
  };

  const setQty = (id, q) => {
    setCart((c) =>
      c
        .map((l) => (l.product === id ? { ...l, quantity: Math.max(0, Number(q) || 0) } : l))
        .filter((l) => l.quantity > 0)
    );
  };
  const removeLine = (id) => setCart((c) => c.filter((l) => l.product !== id));
  const clearCart = () => setCart([]);

  const totals = useMemo(() => {
    let subtotal = 0, tax = 0;
    for (const l of cart) {
      const line = l.unit_price * l.quantity;
      subtotal += line;
      tax += (line * l.tax_rate) / 100;
    }
    return { subtotal, tax, total: subtotal + tax };
  }, [cart]);

  const change = useMemo(() => {
    const given = Number(cashGiven || 0);
    return given > 0 ? given - totals.total : 0;
  }, [cashGiven, totals.total]);

  const submit = async () => {
    if (!till) return notify("err", "Open a till first.");
    if (!cart.length) return notify("err", "Cart is empty.");
    if (payMethod === "cash" && Number(cashGiven || 0) < totals.total)
      return notify("err", "Cash tendered is less than the total.");
    if (payMethod === "mpesa" && !mpesaPhone.trim())
      return notify("err", "Enter the M-Pesa phone number.");

    setSubmitting(true);
    try {
      const body = {
        till_session: till.id,
        customer: customer.trim() || undefined,
        payment_method: payMethod,
        client_uuid: uuid(),
        cart_lines: cart.map((l) => ({
          product_id: l.product,
          quantity: l.quantity,
          unit_price: l.unit_price,
          tax_rate: l.tax_rate,
        })),
      };
      const sale = await apiFetch(ENDPOINTS.sales, { method: "POST", body });

      if (payMethod === "mpesa") {
        try {
          await apiFetch(ENDPOINTS.mpesa, {
            method: "POST",
            body: { sale_id: sale.id, phone_number: mpesaPhone.trim() },
          });
          notify("ok", "M-Pesa STK push sent.");
        } catch (err) {
          notify("err", `Sale saved, but M-Pesa failed: ${err.message}`);
        }
      }

      setLastReceipt({
        number: sale.receipt_number || sale.id,
        date: new Date(),
        customer: customer.trim(),
        paymentMethod: payMethod,
        lines: cart.map((line) => ({ ...line })),
        subtotal: totals.subtotal,
        tax: totals.tax,
        total: totals.total,
        cashGiven: payMethod === "cash" ? Number(cashGiven || 0) : null,
        change,
      });
      onCompleted && onCompleted(sale);
      clearCart();
      setCashGiven("");
      setMpesaPhone("");
    } catch (e) {
      notify("err", e.message || "Could not complete sale.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pos">
      <section className="card pos-products">
        <div className="section-intro">
          <span className="eyebrow">CATALOG</span>
          <h2>Products</h2>
        </div>
        <input
          className="pos-search"
          placeholder="Search name, SKU, or barcode…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        {loading ? (
          <p className="muted">Loading products…</p>
        ) : !query.trim() ? (
          <p className="muted">Search by product name, SKU, or barcode to find items.</p>
        ) : (
          <ul className="product-list">
            {filtered.map((p) => (
              <li key={p.id}>
                <button className="product-row" onClick={() => addToCart(p)}>
                  <div>
                    <strong>{p.name}</strong>
                    <span className="muted-small">{p.sku || p.barcode || "—"} · {getStock(p)} in stock</span>
                  </div>
                  <div className="product-price">{money(getPrice(p))}</div>
                </button>
              </li>
            ))}
            {!filtered.length && <li className="muted">No products match that name, SKU, or barcode.</li>}
          </ul>
        )}
      </section>

      <section className="card pos-cart">
        <div className="section-intro">
          <span className="eyebrow">CART</span>
          <h2>Current sale</h2>
        </div>

        <Field
          label="Customer phone (optional)"
          value={customer}
          onChange={(e) => setCustomer(e.target.value)}
          placeholder="e.g. 254712345678"
        />

        {cart.length === 0 ? (
          <p className="muted">Cart is empty. Tap products to add.</p>
        ) : (
          <ul className="cart-list">
            {cart.map((l) => (
              <li key={l.product} className="cart-line">
                <div className="cart-line-head">
                  <strong>{l.name}</strong>
                  <button className="ghost small" onClick={() => removeLine(l.product)}>Remove</button>
                </div>
                <div className="cart-line-body">
                  <div className="qty">
                    <button onClick={() => setQty(l.product, l.quantity - 1)}>−</button>
                    <input type="number" min="1" value={l.quantity} onChange={(e) => setQty(l.product, e.target.value)} />
                    <button onClick={() => setQty(l.product, l.quantity + 1)}>+</button>
                  </div>
                  <div className="cart-price">{money(l.unit_price * l.quantity)}</div>
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="totals">
          <div><span>Subtotal</span><strong>{money(totals.subtotal)}</strong></div>
          <div><span>Tax</span><strong>{money(totals.tax)}</strong></div>
          <div className="grand"><span>Total</span><strong>{money(totals.total)}</strong></div>
        </div>

        <div className="pay-methods">
          <button className={`pay-chip ${payMethod === "cash" ? "on" : ""}`} onClick={() => setPayMethod("cash")}>Cash</button>
          <button className={`pay-chip ${payMethod === "mpesa" ? "on" : ""}`} onClick={() => setPayMethod("mpesa")}>M-Pesa</button>
        </div>

        {payMethod === "cash" && (
          <div className="pay-extra">
            <Field label="Cash tendered" type="number" step="0.01" value={cashGiven} onChange={(e) => setCashGiven(e.target.value)} />
            <div className="change">
              <span>Change</span>
              <strong className={change < 0 ? "neg" : ""}>{money(change)}</strong>
            </div>
          </div>
        )}

        {payMethod === "mpesa" && (
          <div className="pay-extra">
            <Field label="Phone number" value={mpesaPhone} onChange={(e) => setMpesaPhone(e.target.value)} placeholder="254712345678" />
          </div>
        )}

        <div className="cart-actions">
          <button className="ghost" onClick={clearCart} disabled={!cart.length || submitting}>Clear</button>
          <button className="primary" onClick={submit} disabled={submitting || !cart.length}>
            {submitting ? "Processing…" : `Charge ${money(totals.total)}`}
          </button>
        </div>

        {lastReceipt && (
          <div className="receipt printable-receipt">
            <div className="receipt-head">
              <span className="eyebrow">RECEIPT</span>
              <strong>#{lastReceipt.number}</strong>
              <span>{lastReceipt.date.toLocaleString()}</span>
            </div>
            {lastReceipt.customer && <span>Customer: {lastReceipt.customer}</span>}
            <span>Payment: {lastReceipt.paymentMethod === "mpesa" ? "M-Pesa" : "Cash"}</span>
            <div className="receipt-lines">
              {lastReceipt.lines.map((line) => (
                <div className="receipt-line" key={line.product}>
                  <span>{line.name} x {line.quantity}</span>
                  <strong>{money(line.unit_price * line.quantity)}</strong>
                </div>
              ))}
            </div>
            <div className="receipt-total">
              <div><span>Subtotal</span><strong>{money(lastReceipt.subtotal)}</strong></div>
              <div><span>Tax</span><strong>{money(lastReceipt.tax)}</strong></div>
              <div><span>Total</span><strong>{money(lastReceipt.total)}</strong></div>
              {lastReceipt.cashGiven !== null && <div><span>Cash</span><strong>{money(lastReceipt.cashGiven)}</strong></div>}
              {lastReceipt.cashGiven !== null && <div><span>Change</span><strong>{money(lastReceipt.change)}</strong></div>}
            </div>
            <button className="primary receipt-print" onClick={() => window.print()}>Print receipt</button>
          </div>
        )}
      </section>
    </div>
  );
}

/* ========================================================================
 * INVENTORY PAGE — full CRUD + stock management
 * ===================================================================== */

function InventoryPage({ apiFetch, notify }) {
  const [rows, setRows] = useState([]);
  const [categories, setCategories] = useState([]);
  const [q, setQ] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [modal, setModal] = useState(null); // "create" | "edit" | "stock" | null
  const [editing, setEditing] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [deleteNote, setDeleteNote] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const [p, c] = await Promise.all([
        apiFetch(ENDPOINTS.products),
        apiFetch(ENDPOINTS.categories),
      ]);
      setRows(listOf(p));
      setCategories(listOf(c));
    } catch (e) {
      setLoadError(e.message || "Could not load inventory.");
      notify("err", e.message || "Could not load inventory.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch, notify]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    let out = rows;
    if (s) {
      out = out.filter((r) =>
        [r.name, r.sku, r.barcode].some((v) => String(v || "").toLowerCase().includes(s))
      );
    }
    if (lowOnly) {
      out = out.filter((r) => {
        const rl = getReorder(r);
        return rl > 0 && getStock(r) <= rl;
      });
    }
    return out;
  }, [rows, q, lowOnly]);

  const catName = (p) => {
    if (!p || !p.category) return "—";
    if (typeof p.category === "object") return p.category.name || p.category.title || "—";
    const c = categories.find((x) => x.id === p.category);
    return c?.name || `#${p.category}`;
  };

  const removeProduct = async (p) => {
    if (!deleteReason) return setDeleteError("Select a reason before archiving this product.");
    if (deleteReason === "other" && !deleteNote.trim()) return setDeleteError("Explain why the product is being archived.");
    setDeleting(true);
    setDeleteError("");
    try {
      await apiFetch(`${ENDPOINTS.products}${p.id}/`, {
        method: "DELETE",
        body: { reason: deleteReason, note: deleteNote.trim() },
      });
      notify("ok", "Product archived and reason recorded.");
      setConfirmDelete(null);
      setDeleteReason("");
      setDeleteNote("");
      loadAll();
    } catch (e) {
      setDeleteError(e.message || "Could not archive product.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro">
          <span className="eyebrow">CATALOG</span>
          <h2>Inventory</h2>
          <p>{rows.length} product{rows.length === 1 ? "" : "s"} · {categories.length} categories</p>
        </div>
        <div className="list-tools">
          <input placeholder="Search name or SKU…" value={q} onChange={(e) => setQ(e.target.value)} />
          <label className="toggle">
            <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
            <span>Low stock</span>
          </label>
          <button className="ghost" onClick={loadAll} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
          <button className="primary" onClick={() => { setEditing(null); setModal("create"); }}>+ Add product</button>
        </div>
      </div>

      {loadError && <p className="form-error">{loadError}</p>}
      <Table
        columns={[
          { key: "name", label: "Product" },
          { key: "sku", label: "SKU", render: (r) => r.sku || r.barcode || "—" },
          { key: "category", label: "Category", render: catName },
          { key: "price", label: "Price", render: (r) => money(getPrice(r)) },
          {
            key: "stock",
            label: "Stock",
            render: (r) => {
              const s = getStock(r);
              const rl = getReorder(r);
              const low = rl > 0 && s <= rl;
              return <span className={low ? "stock-low" : ""}>{s}{low ? " ⚠" : ""}</span>;
            },
          },
          {
            key: "actions",
            label: "Actions",
            render: (r) => (
              <div className="row-actions">
                <button className="ghost small" onClick={() => { setEditing(r); setModal("edit"); }}>Edit</button>
                <button className="ghost small" onClick={() => { setEditing(r); setModal("stock"); }}>Stock</button>
                <button className="ghost small danger" onClick={() => { setConfirmDelete(r); setDeleteReason(""); setDeleteNote(""); setDeleteError(""); }}>Archive</button>
              </div>
            ),
          },
        ]}
        rows={filtered}
      />

      {!filtered.length && !loading && (
        <p className="muted">
          {rows.length ? "No products match the filter." : "No products yet. Click “Add product”."}
        </p>
      )}

      <ProductModal
        open={modal === "create" || modal === "edit"}
        mode={modal}
        product={editing}
        categories={categories}
        apiFetch={apiFetch}
        notify={notify}
        onClose={() => { setModal(null); setEditing(null); }}
        onSaved={() => { setModal(null); setEditing(null); loadAll(); }}
        onCategoryCreated={(cat) => setCategories((cs) => [...cs, cat])}
      />

      <StockModal
        open={modal === "stock"}
        product={editing}
        apiFetch={apiFetch}
        notify={notify}
        onClose={() => { setModal(null); setEditing(null); }}
        onSaved={() => { setModal(null); setEditing(null); loadAll(); }}
      />

      <Modal open={Boolean(confirmDelete)} title="Delete product" onClose={() => setConfirmDelete(null)}>
        <p><strong>{confirmDelete?.name}</strong> will be archived and hidden from the catalog. The record is retained for sales history.</p>
        <label className="field">
          <span>Reason for archiving</span>
          <select value={deleteReason} onChange={(e) => setDeleteReason(e.target.value)} required>
            <option value="">Choose a reason</option>
            <option value="discontinued">Discontinued</option>
            <option value="duplicate">Duplicate listing</option>
            <option value="incorrect_item">Incorrect product record</option>
            <option value="other">Other</option>
          </select>
        </label>
        {deleteReason === "other" && <Field label="Explain why" value={deleteNote} onChange={(e) => setDeleteNote(e.target.value)} required />}
        {deleteError && <p className="form-error">{deleteError}</p>}
        <div className="modal-actions">
          <button className="ghost" onClick={() => setConfirmDelete(null)} disabled={deleting}>Cancel</button>
          <button className="danger-btn" onClick={() => removeProduct(confirmDelete)} disabled={deleting}>{deleting ? "Archiving…" : "Archive product"}</button>
        </div>
      </Modal>
    </section>
  );
}

/* ------------------------------------------------------------------------ */
/* Product modal                                                            */
/* ------------------------------------------------------------------------ */

function ProductModal({ open, mode, product, categories, apiFetch, notify, onClose, onSaved, onCategoryCreated }) {
  const isEdit = mode === "edit";
  const [form, setForm] = useState(emptyProduct());
  const [changeReason, setChangeReason] = useState("routine_update");
  const [changeNote, setChangeNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  /* Prefill whenever the modal opens with a product */
  useEffect(() => {
    if (!open) return;
    setError("");
    if (isEdit && product) {
      setChangeReason("routine_update");
      setChangeNote("");
      setForm({
        name: product.name || "",
        sku: product.sku || "",
        barcode: product.barcode || "",
        category: product.category && typeof product.category === "object" ? product.category.id : product.category || "",
        cost_price: product.cost_price ?? product.cost ?? "",
        price: getPrice(product) || "",
        tax_rate: product.tax_rate ?? "",
        stock_quantity: getStock(product),
        reorder_level: product.reorder_level ?? product.reorder_point ?? "",
        unit: product.unit || "",
        description: product.description || "",
        is_active: product.is_active ?? true,
      });
    } else {
      setChangeReason("routine_update");
      setChangeNote("");
      setForm(emptyProduct());
    }
  }, [open, isEdit, product]);

  const set = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [key]: value }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim()) return setError("Name is required.");

    /* Build payload — send the canonical set; unknown fields are ignored by DRF. */
    const payload = {
      name: form.name.trim(),
      sku: form.sku.trim() || undefined,
      barcode: form.barcode.trim() || undefined,
      category: form.category || undefined,
      cost_price: form.cost_price === "" ? undefined : Number(form.cost_price),
      price: form.price === "" ? undefined : Number(form.price),
      tax_rate: form.tax_rate === "" ? undefined : Number(form.tax_rate),
      reorder_level: form.reorder_level === "" ? undefined : Number(form.reorder_level),
      unit: form.unit.trim() || undefined,
      description: form.description.trim() || undefined,
      is_active: form.is_active,
    };
    if (!isEdit) payload.stock_quantity = Number(form.stock_quantity || 0);
    if (isEdit) {
      payload.change_reason = changeReason;
      payload.change_note = changeNote.trim();
      if (changeReason === "other" && !payload.change_note) return setError("Explain the change when the reason is Other.");
    }

    setSaving(true);
    try {
      const path = isEdit ? `${ENDPOINTS.products}${product.id}/` : ENDPOINTS.products;
      await apiFetch(path, { method: isEdit ? "PATCH" : "POST", body: payload });
      notify("ok", isEdit ? "Product updated." : "Product created.");
      onSaved();
    } catch (e) {
      setError(e.message || "Could not save product.");
    } finally {
      setSaving(false);
    }
  };

  const createCategory = async () => {
    const name = window.prompt("New category name:");
    if (!name) return;
    try {
      const cat = await apiFetch(ENDPOINTS.categories, { method: "POST", body: { name } });
      onCategoryCreated(cat);
      setForm((f) => ({ ...f, category: cat.id }));
      notify("ok", "Category created.");
    } catch (e) {
      notify("err", e.message || "Could not create category.");
    }
  };

  return (
    <Modal open={open} title={isEdit ? `Edit: ${product?.name}` : "Add product"} onClose={onClose} wide>
      <form onSubmit={submit} className="form-grid">
        <Field label="Product name *" value={form.name} onChange={set("name")} required />
        <Field label="SKU" value={form.sku} onChange={set("sku")} placeholder="e.g. BEV-001" />
        <Field label="Barcode" value={form.barcode} onChange={set("barcode")} />

        <label className="field">
          <span>Category</span>
          <div className="row-inline">
            <select value={form.category} onChange={set("category")} required>
              <option value="" disabled>Select a category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button type="button" className="ghost small" onClick={createCategory}>+ New</button>
          </div>
        </label>

        <Field label="Cost price (KES)" type="number" step="0.01" min="0" value={form.cost_price} onChange={set("cost_price")} />
        <Field label="Selling price (KES)" type="number" step="0.01" min="0" value={form.price} onChange={set("price")} />
        <Field label="Tax rate (%)" type="number" step="0.01" min="0" value={form.tax_rate} onChange={set("tax_rate")} />
        <Field label="Unit" value={form.unit} onChange={set("unit")} placeholder="pcs, kg, ltr…" />

        {!isEdit && (
          <Field label="Opening stock" type="number" min="0" value={form.stock_quantity} onChange={set("stock_quantity")} />
        )}
        <Field label="Reorder level" type="number" min="0" value={form.reorder_level} onChange={set("reorder_level")} />

        {isEdit && (
          <>
            <label className="field">
              <span>Reason for product change</span>
              <select value={changeReason} onChange={(e) => setChangeReason(e.target.value)} required>
                <option value="routine_update">Routine product update</option>
                <option value="pricing_update">Price or tax update</option>
                <option value="barcode_correction">Barcode or SKU correction</option>
                <option value="data_correction">Product data correction</option>
                <option value="other">Other</option>
              </select>
            </label>
            {changeReason === "other" && <Field label="Explain the change" value={changeNote} onChange={(e) => setChangeNote(e.target.value)} required />}
          </>
        )}

        <label className="field checkbox">
          <input type="checkbox" checked={form.is_active} onChange={set("is_active")} />
          <span>Active (available for sale)</span>
        </label>

        <label className="field grid-full">
          <span>Description</span>
          <textarea value={form.description} onChange={set("description")} rows={3} />
        </label>

        {error && <div className="form-error grid-full">{error}</div>}

        <div className="modal-actions grid-full">
          <button type="button" className="ghost" onClick={onClose} disabled={saving}>Cancel</button>
          <button type="submit" className="primary" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Create product"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function emptyProduct() {
  return {
    name: "",
    sku: "",
    barcode: "",
    category: "",
    cost_price: "",
    price: "",
    tax_rate: "",
    stock_quantity: 0,
    reorder_level: "",
    unit: "",
    description: "",
    is_active: true,
  };
}

/* ------------------------------------------------------------------------ */
/* Stock adjustment modal                                                   */
/* ------------------------------------------------------------------------ */

function StockModal({ open, product, apiFetch, notify, onClose, onSaved }) {
  const [direction, setDirection] = useState("in");
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setDirection("in");
      setQuantity("");
      setReason("");
      setNote("");
      setError("");
    }
  }, [open]);

  if (!product) return null;

  const currentStock = getStock(product);
  const qty = Number(quantity || 0);
  const projected = direction === "in" ? currentStock + qty : currentStock - qty;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (qty <= 0) return setError("Quantity must be greater than zero.");
    if (projected < 0) return setError("Cannot reduce stock below zero.");
    if (!reason) return setError("Select why the stock is changing.");
    if (reason === "other" && !note.trim()) return setError("Explain the stock change when the reason is Other.");

    const body = {
      product_id: product.id,
      counted_quantity: projected,
      reason,
      note: note.trim(),
    };

    setSaving(true);
    try {
      await apiFetch(ENDPOINTS.stockMovements, { method: "POST", body });

      notify("ok", `Stock updated (${currentStock} → ${projected}).`);
      onSaved();
    } catch (e) {
      setError(e.message || "Could not adjust stock.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal open={open} title={`Adjust stock — ${product.name}`} onClose={onClose}>
      <form onSubmit={submit} className="form-grid">
        <div className="stock-summary grid-full">
          <div>
            <span className="eyebrow">Current</span>
            <strong>{currentStock}</strong>
          </div>
          <div>
            <span className="eyebrow">Projected</span>
            <strong className={projected < 0 ? "neg" : ""}>{projected}</strong>
          </div>
        </div>

        <label className="field">
          <span>Direction</span>
          <div className="segmented">
            <button type="button" className={direction === "in" ? "on" : ""} onClick={() => setDirection("in")}>Incoming</button>
            <button type="button" className={direction === "out" ? "on" : ""} onClick={() => setDirection("out")}>Outgoing</button>
          </div>
        </label>

        <Field
          label="Quantity"
          type="number"
          min="1"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          required
        />

        <label className="field">
          <span>Reason for stock change</span>
          <select value={reason} onChange={(e) => setReason(e.target.value)} required>
            <option value="">Choose a reason</option>
            <option value="restock">Restock / delivery</option>
            <option value="sale">Sale correction / manual sale</option>
            <option value="damage">Damaged goods</option>
            <option value="expiry">Expired goods</option>
            <option value="theft">Loss / theft</option>
            <option value="correction">Stock count correction</option>
            <option value="customer_return">Customer return</option>
            <option value="transfer">Transfer</option>
            <option value="other">Other</option>
          </select>
        </label>
        {(reason === "other" || reason === "damage" || reason === "expiry" || reason === "theft") && (
          <Field label={reason === "other" ? "Explain the stock change" : "Notes (optional)"} value={note} onChange={(e) => setNote(e.target.value)} required={reason === "other"} />
        )}

        {error && <div className="form-error grid-full">{error}</div>}

        <div className="modal-actions grid-full">
          <button type="button" className="ghost" onClick={onClose} disabled={saving}>Cancel</button>
          <button type="submit" className="primary" disabled={saving}>
            {saving ? "Saving…" : `Apply (${direction === "in" ? "+" : "−"}${qty})`}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/* ========================================================================
 * Sales list, reports, simple lists, table
 * ===================================================================== */

function SalesList({ apiFetch, notify }) {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch(ENDPOINTS.sales);
      setRows(listOf(data));
    } catch (e) {
      notify("err", e.message || "Could not load sales.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch, notify]);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    const s = q.toLowerCase();
    if (!s) return rows;
    return rows.filter((r) => String(r.receipt_number || r.id || "").toLowerCase().includes(s));
  }, [rows, q]);

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro">
          <span className="eyebrow">HISTORY</span>
          <h2>Sales</h2>
        </div>
        <div className="list-tools">
          <input placeholder="Search receipt…" value={q} onChange={(e) => setQ(e.target.value)} />
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        </div>
      </div>
      <Table
        columns={[
          { key: "receipt_number", label: "Receipt" },
          { key: "created_at", label: "Date", render: (r) => r.created_at ? new Date(r.created_at).toLocaleString() : "—" },
          { key: "payment_method", label: "Payment" },
          { key: "payment_status", label: "Status" },
          { key: "total_amount", label: "Total", render: (r) => money(r.total_amount) },
        ]}
        rows={filtered}
      />
    </section>
  );
}

function CustomersPage({ apiFetch, notify }) {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState({ name: "", phone_number: "" });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(listOf(await apiFetch(ENDPOINTS.customers)));
    } catch (e) {
      setError(e.message || "Could not load customers.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await apiFetch(ENDPOINTS.customers, { method: "POST", body: form });
      notify("ok", "Customer saved.");
      setForm({ name: "", phone_number: "" });
      await load();
    } catch (err) {
      setError(err.message || "Could not save customer.");
    } finally {
      setSaving(false);
    }
  };

  const filtered = rows.filter((row) =>
    `${row.name} ${row.phone_number}`.toLowerCase().includes(query.trim().toLowerCase())
  );

  return (
    <>
      <section className="card">
        <div className="section-intro">
          <span className="eyebrow">CUSTOMER DIRECTORY</span>
          <h2>Customers</h2>
          <p>Save customer details for lookup at checkout and review their paid sales.</p>
        </div>
        <form className="form-grid" onSubmit={submit}>
          <Field label="Customer name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <Field label="Phone number" type="tel" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} required />
          {error && <div className="form-error grid-full">{error}</div>}
          <button className="primary grid-full" disabled={saving}>{saving ? "Saving…" : "Save customer"}</button>
        </form>
      </section>
      <section className="card">
        <div className="list-head">
          <div className="section-intro"><h2>Customer records</h2><p>{rows.length} customer{rows.length === 1 ? "" : "s"}</p></div>
          <div className="list-tools">
            <input placeholder="Search name or phone…" value={query} onChange={(e) => setQuery(e.target.value)} />
            <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
          </div>
        </div>
        {error && !rows.length ? <p className="form-error">{error}</p> : loading ? <p className="muted">Loading customers…</p> : !filtered.length ? <p className="muted">{rows.length ? "No customers match that search." : "No customers yet. Add one above or save a customer during checkout."}</p> : (
          <Table columns={[
            { key: "name", label: "Name" },
            { key: "phone_number", label: "Phone" },
            { key: "sales_count", label: "Completed sales" },
            { key: "total_spent", label: "Paid sales", render: (row) => money(row.total_spent) },
            { key: "loyalty_points", label: "Loyalty points" },
          ]} rows={filtered} />
        )}
      </section>
    </>
  );
}

function AuditPage({ apiFetch }) {
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(listOf(await apiFetch(ENDPOINTS.audit)));
    } catch (e) {
      setError(e.message || "Could not load the audit log.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);
  useEffect(() => { load(); }, [load]);

  const filtered = rows.filter((row) =>
    `${row.actor} ${row.action} ${row.model_name} ${row.object_id} ${JSON.stringify(row.changes || {})}`.toLowerCase().includes(query.trim().toLowerCase())
  );
  const actionLabel = (action) => ({
    added: "Added",
    sold: "Sold",
    deleted: "Deleted / archived",
    stock_added: "Stock added",
    stock_removed: "Stock removed",
    sale_voided: "Sale voided",
    received: "Goods received",
    open: "Till opened",
    close: "Till closed",
    updated: "Updated",
  }[action] || title(action));
  const flattenChanges = (value, prefix = "") => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      return Object.entries(value).flatMap(([key, nested]) => flattenChanges(nested, prefix ? `${prefix} · ${title(key)}` : title(key)));
    }
    if (Array.isArray(value)) return [[prefix, value.map((item) => String(item)).join(", ")]];
    const isReason = /(^| · )(Reason|Deletion type)$/.test(prefix);
    return [[prefix, isReason && value ? title(String(value)) : String(value ?? "—")]];
  };

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro"><span className="eyebrow">ACTIVITY</span><h2>Audit log</h2><p>Records are created for sales, customers, stock changes, and purchasing activity.</p></div>
        <div className="list-tools">
          <input placeholder="Search activity…" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        </div>
      </div>
      {error ? <p className="form-error">{error}</p> : loading ? <p className="muted">Loading audit events…</p> : !filtered.length ? <p className="muted">{rows.length ? "No audit events match that search." : "No recorded activity yet. New changes will appear here."}</p> : (
        <Table columns={[
          { key: "created_at", label: "When", render: (row) => row.created_at ? new Date(row.created_at).toLocaleString() : "—" },
          { key: "actor", label: "User" },
          { key: "action", label: "Action", render: (row) => actionLabel(row.action) },
          { key: "model_name", label: "Record type" },
          { key: "object_id", label: "Record ID" },
          {
            key: "changes",
            label: "Changes",
            render: (row) => {
              const changes = row.changes && typeof row.changes === "object" ? flattenChanges(row.changes) : [];
              if (!changes.length) return "—";
              return (
                <ul className="audit-changes">
                  {changes.map(([key, value], index) => (
                    <li key={`${key}-${index}`}><strong>{key}:</strong> {value}</li>
                  ))}
                </ul>
              );
            },
          },
          { key: "ip_address", label: "IP" },
        ]} rows={filtered} />
      )}
    </section>
  );
}

function NotificationsPage({ apiFetch, notify }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRows(listOf(await apiFetch(ENDPOINTS.notifications)));
    } catch (e) {
      setError(e.message || "Could not load notifications.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);
  useEffect(() => { load(); }, [load]);

  const markRead = async (ids) => {
    if (!ids.length) return;
    try {
      await apiFetch(ENDPOINTS.notificationsRead, { method: "POST", body: { ids } });
      const readAt = new Date().toISOString();
      setRows((current) => current.map((row) => ids.includes(row.id) ? { ...row, read_at: readAt } : row));
      notify("ok", "Notification marked as read.");
    } catch (e) {
      notify("err", e.message || "Could not update notification.");
    }
  };

  const unreadIds = rows.filter((row) => !row.read_at).map((row) => row.id);

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro"><span className="eyebrow">ALERTS</span><h2>Notifications</h2><p>{unreadIds.length} unread alert{unreadIds.length === 1 ? "" : "s"}</p></div>
        <div className="list-tools">
          {unreadIds.length > 0 && <button className="secondary" onClick={() => markRead(unreadIds)}>Mark all read</button>}
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        </div>
      </div>
      {error ? <p className="form-error">{error}</p> : loading ? <p className="muted">Loading notifications…</p> : !rows.length ? <p className="muted">No alerts yet. Low-stock alerts are created automatically when stock reaches its reorder level.</p> : (
        <Table columns={[
          { key: "created_at", label: "When", render: (row) => row.created_at ? new Date(row.created_at).toLocaleString() : "—" },
          { key: "type", label: "Type", render: (row) => title(row.type) },
          { key: "message", label: "Message" },
          { key: "reference_id", label: "Related record" },
          { key: "read_at", label: "Status", render: (row) => row.read_at ? "Read" : "Unread" },
          { key: "action", label: "Action", render: (row) => row.read_at ? "—" : <button className="ghost small" onClick={() => markRead([row.id])}>Mark read</button> },
        ]} rows={rows} />
      )}
    </section>
  );
}

function PurchasingPage({ apiFetch, notify }) {
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [supplierForm, setSupplierForm] = useState({ name: "", phone: "", email: "" });
  const [showSupplierForm, setShowSupplierForm] = useState(false);
  const [supplierSaving, setSupplierSaving] = useState(false);
  const [creating, setCreating] = useState(false);
  const [savingOrder, setSavingOrder] = useState(false);
  const [draft, setDraft] = useState({ supplier: "", expected_date: "", lines: [] });
  const [receiving, setReceiving] = useState(null);
  const [receiptLines, setReceiptLines] = useState([]);
  const [deliveryNoteRef, setDeliveryNoteRef] = useState("");
  const [receivingBusy, setReceivingBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [orderData, supplierData, productData] = await Promise.all([
        apiFetch(ENDPOINTS.purchases),
        apiFetch(ENDPOINTS.suppliers),
        apiFetch(ENDPOINTS.products),
      ]);
      setOrders(listOf(orderData));
      setSuppliers(listOf(supplierData));
      setProducts(listOf(productData));
    } catch (e) {
      setError(e.message || "Could not load purchasing records.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);
  useEffect(() => { load(); }, [load]);

  const addSupplier = async (e) => {
    e.preventDefault();
    setSupplierSaving(true);
    setError("");
    try {
      const supplier = await apiFetch(ENDPOINTS.suppliers, { method: "POST", body: supplierForm });
      setSuppliers((current) => [...current, supplier].sort((a, b) => a.name.localeCompare(b.name)));
      setSupplierForm({ name: "", phone: "", email: "" });
      setShowSupplierForm(false);
      notify("ok", "Supplier saved.");
    } catch (e2) {
      setError(e2.message || "Could not save supplier.");
    } finally {
      setSupplierSaving(false);
    }
  };

  const startOrder = () => {
    setError("");
    setDraft({
      supplier: suppliers[0] ? String(suppliers[0].id) : "",
      expected_date: "",
      lines: products.length ? [{ product_id: String(products[0].id), quantity_ordered: "1", unit_cost: products[0].cost_price || "0" }] : [],
    });
    setCreating(true);
  };

  const updateDraftLine = (index, key, value) => {
    setDraft((current) => ({
      ...current,
      lines: current.lines.map((line, i) => {
        if (i !== index) return line;
        if (key === "product_id") {
          const product = products.find((item) => String(item.id) === String(value));
          return { ...line, product_id: value, unit_cost: product?.cost_price || "0" };
        }
        return { ...line, [key]: value };
      }),
    }));
  };

  const createOrder = async (e) => {
    e.preventDefault();
    setSavingOrder(true);
    setError("");
    try {
      await apiFetch(ENDPOINTS.purchases, {
        method: "POST",
        body: {
          supplier: draft.supplier,
          expected_date: draft.expected_date || undefined,
          lines: draft.lines.map((line) => ({
            product_id: line.product_id,
            quantity_ordered: Number(line.quantity_ordered),
            unit_cost: Number(line.unit_cost),
          })),
        },
      });
      notify("ok", "Purchase order created.");
      setCreating(false);
      await load();
    } catch (e2) {
      setError(e2.message || "Could not create purchase order.");
    } finally {
      setSavingOrder(false);
    }
  };

  const startReceiving = (order) => {
    setReceiving(order);
    setDeliveryNoteRef("");
    setReceiptLines(order.lines.filter((line) => line.quantity_remaining > 0).map((line) => ({
      product_id: line.product_id,
      product: line.product,
      quantity_remaining: line.quantity_remaining,
      quantity_received: "",
    })));
  };

  const receiveOrder = async (e) => {
    e.preventDefault();
    const lines = receiptLines.filter((line) => Number(line.quantity_received) > 0).map((line) => ({
      product_id: line.product_id,
      quantity_received: Number(line.quantity_received),
    }));
    if (!lines.length) return setError("Enter at least one received quantity.");
    setReceivingBusy(true);
    setError("");
    try {
      await apiFetch(ENDPOINTS.purchaseReceive, {
        method: "POST",
        body: { purchase_order_id: receiving.id, lines, delivery_note_ref: deliveryNoteRef.trim() },
      });
      notify("ok", "Goods received and inventory updated.");
      setReceiving(null);
      await load();
    } catch (e2) {
      setError(e2.message || "Could not receive goods.");
    } finally {
      setReceivingBusy(false);
    }
  };

  const orderColumns = [
    { key: "id", label: "Order", render: (row) => `PO-${row.id}` },
    { key: "supplier", label: "Supplier" },
    { key: "status", label: "Status", render: (row) => title(row.status) },
    { key: "expected_date", label: "Expected", render: (row) => row.expected_date || "—" },
    { key: "created_by", label: "Created by" },
    { key: "lines", label: "Products", render: (row) => row.lines.length },
    { key: "total", label: "Order value", render: (row) => money(row.lines.reduce((sum, line) => sum + Number(line.quantity_ordered) * Number(line.unit_cost), 0)) },
    { key: "actions", label: "Actions", render: (row) => row.status === "fully_received" || row.status === "cancelled" ? "—" : <button className="ghost small" onClick={() => startReceiving(row)}>Receive goods</button> },
  ];

  return (
    <>
      <section className="card">
        <div className="list-head">
          <div className="section-intro"><span className="eyebrow">SUPPLIERS</span><h2>Purchasing</h2><p>Create orders, receive deliveries, and update inventory from received quantities.</p></div>
          <div className="list-tools">
            <button className="secondary" onClick={() => setShowSupplierForm((value) => !value)}>{showSupplierForm ? "Cancel supplier" : "+ Add supplier"}</button>
            <button className="primary" onClick={startOrder} disabled={!suppliers.length || !products.length}>+ New order</button>
            <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
          </div>
        </div>
        <p className="muted">{suppliers.length} active supplier{suppliers.length === 1 ? "" : "s"} · {orders.length} purchase order{orders.length === 1 ? "" : "s"}</p>
        {showSupplierForm && (
          <form className="form-grid" onSubmit={addSupplier}>
            <Field label="Supplier name" value={supplierForm.name} onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })} required />
            <Field label="Phone" type="tel" value={supplierForm.phone} onChange={(e) => setSupplierForm({ ...supplierForm, phone: e.target.value })} />
            <Field label="Email" type="email" value={supplierForm.email} onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })} />
            <button className="primary grid-full" disabled={supplierSaving}>{supplierSaving ? "Saving…" : "Save supplier"}</button>
          </form>
        )}
        {error && !creating && !receiving && <p className="form-error">{error}</p>}
      </section>
      <section className="card">
        <div className="section-intro"><h2>Purchase orders</h2></div>
        {loading ? <p className="muted">Loading purchase orders…</p> : !orders.length ? <p className="muted">No purchase orders yet. Add a supplier, then create an order.</p> : <Table columns={orderColumns} rows={orders} />}
      </section>

      <Modal open={creating} title="Create purchase order" onClose={() => setCreating(false)} wide>
        <form onSubmit={createOrder} className="form-grid">
          <label className="field">
            <span>Supplier</span>
            <select value={draft.supplier} onChange={(e) => setDraft({ ...draft, supplier: e.target.value })} required>
              <option value="" disabled>Select a supplier</option>
              {suppliers.map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}
            </select>
          </label>
          <Field label="Expected delivery date" type="date" value={draft.expected_date} onChange={(e) => setDraft({ ...draft, expected_date: e.target.value })} />
          <div className="grid-full">
            <div className="list-head"><strong>Order lines</strong><button type="button" className="secondary" onClick={() => setDraft({ ...draft, lines: [...draft.lines, { product_id: String(products[0]?.id || ""), quantity_ordered: "1", unit_cost: products[0]?.cost_price || "0" }] })}>+ Add product</button></div>
            {draft.lines.map((line, index) => (
              <div className="form-grid" key={`${index}-${line.product_id}`}>
                <label className="field">
                  <span>Product</span>
                  <select value={line.product_id} onChange={(e) => updateDraftLine(index, "product_id", e.target.value)} required>
                    {products.map((product) => <option key={product.id} value={product.id}>{product.name} · {product.sku}</option>)}
                  </select>
                </label>
                <Field label="Quantity" type="number" min="1" step="1" value={line.quantity_ordered} onChange={(e) => updateDraftLine(index, "quantity_ordered", e.target.value)} required />
                <Field label="Unit cost (KES)" type="number" min="0" step="0.01" value={line.unit_cost} onChange={(e) => updateDraftLine(index, "unit_cost", e.target.value)} required />
                <button type="button" className="ghost small danger" onClick={() => setDraft({ ...draft, lines: draft.lines.filter((_, i) => i !== index) })} disabled={draft.lines.length <= 1}>Remove</button>
              </div>
            ))}
          </div>
          {error && <div className="form-error grid-full">{error}</div>}
          <div className="modal-actions grid-full">
            <button type="button" className="ghost" onClick={() => setCreating(false)}>Cancel</button>
            <button type="submit" className="primary" disabled={savingOrder}>{savingOrder ? "Creating…" : "Create order"}</button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(receiving)} title={`Receive goods — PO-${receiving?.id || ""}`} onClose={() => setReceiving(null)} wide>
        <form onSubmit={receiveOrder} className="form-grid">
          <Field label="Delivery note reference" value={deliveryNoteRef} onChange={(e) => setDeliveryNoteRef(e.target.value)} />
          {receiptLines.map((line, index) => (
            <div className="form-grid grid-full" key={line.product_id}>
              <div className="field"><span>Product</span><strong>{line.product}</strong><small>{line.quantity_remaining} remaining on order</small></div>
              <Field label="Quantity received now" type="number" min="0" max={line.quantity_remaining} step="1" value={line.quantity_received} onChange={(e) => setReceiptLines((current) => current.map((item, i) => i === index ? { ...item, quantity_received: e.target.value } : item))} />
            </div>
          ))}
          {error && <div className="form-error grid-full">{error}</div>}
          <div className="modal-actions grid-full">
            <button type="button" className="ghost" onClick={() => setReceiving(null)}>Cancel</button>
            <button type="submit" className="primary" disabled={receivingBusy}>{receivingBusy ? "Receiving…" : "Record receipt"}</button>
          </div>
        </form>
      </Modal>
    </>
  );
}

function SimpleList({ title: heading, endpoint, apiFetch, notify, columns }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch(endpoint);
      setRows(listOf(data));
    } catch (e) {
      notify("err", e.message || "Could not load data.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch, endpoint, notify]);

  useEffect(() => { load(); }, [load]);

  const inferred = useMemo(() => {
    if (columns) return columns.map((k) => ({ key: k, label: title(k) }));
    if (!rows.length) return [];
    return Object.keys(rows[0]).slice(0, 6).map((k) => ({ key: k, label: title(k) }));
  }, [rows, columns]);

  return (
    <section className="card">
      <div className="list-head">
        <div className="section-intro">
          <span className="eyebrow">DATA</span>
          <h2>{heading}</h2>
        </div>
        <div className="list-tools">
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
        </div>
      </div>
      <Table columns={inferred} rows={rows} />
    </section>
  );
}

function Table({ columns, rows }) {
  if (!rows.length) return null;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id ?? i}>
              {columns.map((c) => (
                <td key={c.key}>{c.render ? c.render(r) : String(r[c.key] ?? "—")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Reports({ apiFetch, notify }) {
  const [data, setData] = useState(null);
  const [period, setPeriod] = useState("daily");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await apiFetch(`${ENDPOINTS.salesReport}?period=${period}`));
    } catch (e) {
      notify("err", e.message || "Could not load reports.");
    } finally {
      setLoading(false);
    }
  }, [apiFetch, notify, period]);

  useEffect(() => { load(); }, [load]);

  const summary = data?.summary || {};

  return (
    <section className="reports-page">
      <section className="card no-print">
      <div className="list-head">
        <div className="section-intro">
          <span className="eyebrow">INSIGHTS</span>
          <h2>Reports</h2>
          <p>Paid, completed sales · {data ? `${data.start} to ${data.end}` : "Choose a period"}</p>
        </div>
        <div className="list-tools">
          <label className="field report-period">
            <span>Report period</span>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </label>
          <button className="ghost" onClick={load} disabled={loading}>{loading ? "Loading…" : "Refresh"}</button>
          <button className="primary" onClick={() => window.print()} disabled={!data}>Print report</button>
        </div>
      </div>
      </section>
      {loading && !data ? <section className="card"><p className="muted">Preparing report…</p></section> : !data ? <section className="card"><p className="muted">No report data available.</p></section> : (
        <>
          <header className="report-print-head">
            <span className="eyebrow">TENANT POS · SALES REPORT</span>
            <h2>{title(data.period)} report</h2>
            <p>{data.start} – {data.end}</p>
          </header>
          <section className="stat-grid report-summary">
            <div className="stat"><span className="eyebrow">Paid revenue</span><strong>{money(summary.revenue)}</strong></div>
            <div className="stat"><span className="eyebrow">Transactions</span><strong>{summary.transactions ?? 0}</strong></div>
            <div className="stat"><span className="eyebrow">Average sale</span><strong>{money(summary.average_sale)}</strong></div>
            <div className="stat"><span className="eyebrow">Cash / M-Pesa</span><strong>{money(summary.cash_revenue)} / {money(summary.mpesa_revenue)}</strong></div>
          </section>
          <section className="card report-chart-card">
            <div className="section-intro"><h2>Revenue trend</h2><p>Paid sales by {data.bucket}</p></div>
            <ReportChart series={data.series} valueKey="revenue" formatValue={(value) => money(value)} color="#2563eb" />
          </section>
          <section className="card report-chart-card">
            <div className="section-intro"><h2>Transaction volume</h2><p>Completed paid transactions by {data.bucket}</p></div>
            <ReportChart series={data.series} valueKey="transactions" formatValue={(value) => String(value)} color="#0f766e" />
          </section>
          <section className="card report-data-card">
            <div className="section-intro"><h2>Period breakdown</h2></div>
            <Table columns={[
              { key: "label", label: "Period" },
              { key: "revenue", label: "Paid revenue", render: (row) => money(row.revenue) },
              { key: "transactions", label: "Transactions" },
            ]} rows={data.series} />
          </section>
        </>
      )}
    </section>
  );
}

function ReportChart({ series, valueKey, formatValue, color }) {
  const width = 800;
  const height = 250;
  const left = 58;
  const right = 18;
  const top = 18;
  const bottom = 52;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const values = series.map((item) => Number(item[valueKey] || 0));
  const maximum = Math.max(...values, 1);
  const slotWidth = plotWidth / Math.max(series.length, 1);
  const barWidth = Math.max(3, Math.min(28, slotWidth * 0.62));
  const labelStep = Math.max(1, Math.ceil(series.length / 8));

  return (
    <div className="report-chart-scroll">
      <svg className="report-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${valueKey} by period chart`}>
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
          const y = top + plotHeight * (1 - fraction);
          return (
            <g key={fraction}>
              <line x1={left} y1={y} x2={width - right} y2={y} stroke="#e5e7eb" />
              <text x={left - 8} y={y + 4} textAnchor="end" className="chart-axis-label">
                {formatValue(maximum * fraction)}
              </text>
            </g>
          );
        })}
        {series.map((item, index) => {
          const value = values[index];
          const barHeight = (value / maximum) * plotHeight;
          const x = left + slotWidth * index + (slotWidth - barWidth) / 2;
          const y = top + plotHeight - barHeight;
          return (
            <g key={item.date}>
              <title>{`${item.label}: ${formatValue(value)}`}</title>
              <rect x={x} y={y} width={barWidth} height={Math.max(1, barHeight)} rx="3" fill={color} />
              {(index % labelStep === 0 || index === series.length - 1) && (
                <text x={left + slotWidth * index + slotWidth / 2} y={height - 20} textAnchor="middle" className="chart-axis-label">
                  {item.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function Field({ label, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input {...props} />
    </label>
  );
}

/* ========================================================================
 * CSS
 * ===================================================================== */

const css = `
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #17202a;
  background: #f5f7fa;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}
* { box-sizing: border-box; }
html, body { margin: 0; min-height: 100%; }
body { background: #f5f7fa; min-width: 320px; min-height: 100vh; }
button, input, textarea, select { font: inherit; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: 0.55; }
.app { min-height: 100vh; }

/* top bar */
.topbar { display: flex; flex-direction: column; gap: 16px; padding: 18px 24px; background: #111827; color: #fff; }
.brand h1 { margin: 5px 0 4px; font-size: 22px; letter-spacing: -0.02em; }
.brand p { margin: 0; color: #aeb7c5; font-size: 13px; }
.topbar-right { display: flex; flex-direction: column; gap: 10px; }
.ghost { padding: 8px 12px; border: 1px solid #374151; background: transparent; color: #fff; border-radius: 8px; font-size: 13px; font-weight: 650; }
.ghost:hover { background: #1f2937; }
.card .ghost, .modal .ghost, .till-bar .ghost { border-color: #9ca3af; color: #1f2937; background: #fff; }
.card .ghost:hover, .modal .ghost:hover, .till-bar .ghost:hover { background: #f3f4f6; border-color: #6b7280; }
.ghost.small { padding: 5px 9px; font-size: 12px; border-color: #d1d5db; color: #374151; background: #fff; }
.ghost.small:hover { background: #f3f4f6; }
.ghost.small.danger { color: #b42318; border-color: #fecaca; }
.ghost.small.danger:hover { background: #fef2f2; }
.till-badge { display: flex; align-items: center; gap: 10px; padding: 8px 12px; background: #1f2937; border-radius: 10px; }
.till-badge strong { display: block; font-size: 13px; }
.till-badge span { display: block; font-size: 11px; color: #9ca3af; }
.till-dot { width: 9px; height: 9px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25); }
.api-control { display: flex; flex-direction: column; gap: 6px; }
.api-control > span { color: #d1d5db; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
.api-control input { padding: 9px 11px; border: 1px solid #374151; border-radius: 8px; background: #1f2937; color: #fff; outline: none; }
.api-control input:focus { border-color: #9ca3af; }

/* layout */
.layout { display: flex; flex-direction: column; }
.content { width: 100%; max-width: 1200px; margin: 0 auto; padding: 18px; }
.sidebar { display: flex; flex-direction: column; background: #fff; border-bottom: 1px solid #e5e7eb; }
.navigation { display: flex; gap: 6px; padding: 10px; overflow-x: auto; }
.nav { flex: 0 0 auto; padding: 9px 13px; border: 0; border-radius: 8px; background: transparent; color: #4b5563; font-size: 13px; font-weight: 650; text-align: left; }
.nav:hover { background: #f3f4f6; color: #111827; }
.nav.active { background: #111827; color: #fff; }
.sidebar-foot { padding: 12px 16px; border-top: 1px solid #e5e7eb; display: none; }
.sidebar-foot strong { display: block; font-size: 13px; margin: 2px 0 3px; }
.muted-small { color: #6b7280; font-size: 12px; }
.muted { color: #6b7280; font-size: 13px; }
.audit-changes { margin: 0; padding-left: 16px; min-width: 220px; font-size: 12px; line-height: 1.5; }
.audit-changes li { overflow-wrap: anywhere; }
.report-period { min-width: 150px; margin-top: 0; }
.report-period select { min-height: 40px; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; color: #111827; }
.report-print-head { display: none; }
.report-chart-card, .report-data-card { margin-top: 14px; }
.report-chart-scroll { overflow-x: auto; margin-top: 16px; }
.report-chart { display: block; width: 100%; min-width: 620px; height: auto; }
.chart-axis-label { fill: #6b7280; font-size: 10px; }
.report-summary .stat strong { font-size: 18px; }

/* cards */
.card { padding: 20px; border: 1px solid #e5e7eb; border-radius: 14px; background: #fff; box-shadow: 0 6px 25px rgba(17, 24, 39, 0.045); }
.center-card { max-width: 520px; margin: 40px auto; }
.section-intro h2 { margin: 5px 0 6px; font-size: 20px; letter-spacing: -0.02em; }
.section-intro p { margin: 0; color: #6b7280; font-size: 13px; }
.eyebrow { display: block; color: #6b7280; font-size: 10px; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; }

/* forms */
.field { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.field span { color: #374151; font-size: 12px; font-weight: 700; }
.field input, .field select, .field textarea {
  min-height: 40px; padding: 9px 11px; border: 1px solid #d1d5db;
  border-radius: 8px; outline: none; background: #fff; color: #111827;
  font-family: inherit;
}
.field textarea { min-height: 70px; resize: vertical; }
.field input:focus, .field select:focus, .field textarea:focus { border-color: #6b7280; box-shadow: 0 0 0 3px rgba(107,114,128,0.12); }
.field.checkbox { flex-direction: row; align-items: center; gap: 8px; }
.field.checkbox input { min-height: auto; width: 16px; height: 16px; }
.field.checkbox span { font-size: 13px; font-weight: 650; }

.form-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
.grid-full { grid-column: 1 / -1; }

.primary, .secondary, .danger-btn {
  min-height: 40px; padding: 9px 14px; border: 0; border-radius: 8px;
  font-size: 13px; font-weight: 750;
}
.primary { background: #111827; color: #fff; }
.primary:hover:not(:disabled) { transform: translateY(-1px); }
.secondary { background: #e5e7eb; color: #111827; }
.danger-btn { background: #b42318; color: #fff; }
.wide { width: 100%; margin-top: 16px; }
.link-button { display: block; margin: 12px auto 0; padding: 6px; border: 0; background: transparent; color: #374151; font-size: 13px; font-weight: 650; text-decoration: underline; }

/* auth */
.auth-shell { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.auth-card { width: 100%; max-width: 460px; }
.brand-center { text-align: center; margin-bottom: 12px; }
.brand-center h1 { margin: 6px 0 4px; font-size: 24px; letter-spacing: -0.02em; }
.brand-center p { margin: 0; color: #6b7280; font-size: 13px; }

/* dashboard */
.stat-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 20px; }
.stat { padding: 14px; border: 1px solid #e5e7eb; border-radius: 10px; background: #f8fafc; }
.stat strong { display: block; margin-top: 6px; font-size: 20px; }
.quick-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }

/* POS */
.pos { display: grid; grid-template-columns: 1fr; gap: 14px; }
.pos-search { width: 100%; margin-top: 12px; padding: 11px 13px; border: 1px solid #d1d5db; border-radius: 10px; outline: none; }
.pos-search:focus { border-color: #6b7280; box-shadow: 0 0 0 3px rgba(107,114,128,0.12); }
.product-list { list-style: none; margin: 12px 0 0; padding: 0; max-height: 520px; overflow: auto; border-top: 1px solid #e5e7eb; }
.product-list li { border-bottom: 1px solid #eef1f5; }
.product-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; width: 100%; padding: 12px 4px; border: 0; background: transparent; text-align: left; }
.product-row:hover { background: #f8fafc; }
.product-row strong { display: block; font-size: 13px; }
.product-price { font-weight: 750; font-size: 13px; }
.cart-customer { margin-top: 12px; }
.cart-list { list-style: none; margin: 12px 0 0; padding: 0; }
.cart-line { padding: 12px 0; border-bottom: 1px solid #eef1f5; }
.cart-line-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.cart-line-head strong { font-size: 13px; }
.cart-line-body { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; gap: 8px; }
.qty { display: inline-flex; align-items: center; gap: 4px; }
.qty button { width: 28px; height: 28px; border: 1px solid #d1d5db; background: #fff; border-radius: 6px; font-size: 15px; line-height: 1; }
.qty input { width: 54px; text-align: center; padding: 5px; border: 1px solid #d1d5db; border-radius: 6px; }
.cart-price { font-weight: 750; font-size: 13px; }
.totals { margin-top: 16px; border-top: 1px solid #e5e7eb; padding-top: 12px; }
.totals > div { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; color: #374151; }
.totals .grand { font-size: 16px; margin-top: 6px; border-top: 1px dashed #d1d5db; padding-top: 10px; }
.totals .grand strong { font-size: 18px; }
.pay-methods { display: flex; gap: 8px; margin-top: 14px; }
.pay-chip { flex: 1; padding: 10px; border: 1px solid #d1d5db; background: #fff; border-radius: 8px; font-weight: 700; font-size: 13px; }
.pay-chip.on { background: #111827; color: #fff; border-color: #111827; }
.segmented { display: flex; gap: 6px; margin-top: 12px; }
.segmented button { padding: 8px 14px; border: 1px solid #9ca3af; border-radius: 8px; background: #fff; color: #1f2937; font-size: 13px; font-weight: 700; }
.segmented button.on { background: #111827; border-color: #111827; color: #fff; }
.pay-extra { margin-top: 12px; }
.change { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #f8fafc; font-size: 13px; }
.change strong { font-size: 15px; }
.change strong.neg { color: #b42318; }
.cart-actions { display: flex; justify-content: space-between; gap: 8px; margin-top: 16px; }
.cart-actions .primary { flex: 1; }
.cart-actions .ghost { border-color: #d1d5db; color: #374151; }
.cart-actions .ghost:hover { background: #f3f4f6; }
.receipt { margin-top: 16px; padding: 12px; border: 1px dashed #22c55e; border-radius: 10px; background: #f0fdf4; display: flex; flex-direction: column; gap: 4px; }
.receipt strong { font-size: 16px; }
.receipt-head { display: flex; flex-direction: column; gap: 3px; padding-bottom: 8px; border-bottom: 1px dashed #86efac; }
.receipt-head span:last-child { color: #6b7280; font-size: 11px; }
.receipt-lines { margin-top: 8px; padding: 8px 0; border-top: 1px solid #dcfce7; border-bottom: 1px solid #dcfce7; }
.receipt-line, .receipt-total > div { display: flex; justify-content: space-between; gap: 12px; padding: 3px 0; font-size: 12px; }
.receipt-line strong, .receipt-total strong { font-size: 12px; }
.receipt-total { padding-top: 5px; }
.receipt-total > div:last-child { font-weight: 800; }
.receipt-print { margin-top: 10px; }

@media print {
  body * { visibility: hidden; }
  .printable-receipt, .printable-receipt * { visibility: visible; }
  .printable-receipt { position: absolute; left: 0; top: 0; width: 80mm; margin: 0; padding: 8mm; border: 0; background: #fff; color: #000; box-shadow: none; }
  .receipt-print { display: none; }
  .reports-page, .reports-page * { visibility: visible; }
  .reports-page { position: absolute; inset: 0; width: 100%; padding: 0; color: #111827; }
  .reports-page .no-print { display: none; }
  .reports-page .report-print-head { display: block; margin-bottom: 14px; }
  .reports-page .card { margin-top: 10px; padding: 12px; border: 1px solid #d1d5db; box-shadow: none; break-inside: avoid; }
  .reports-page .report-chart { min-width: 0; width: 100%; }
  .reports-page .table-wrap { overflow: visible; }
  .reports-page table { font-size: 10px; }
  .reports-page th, .reports-page td { padding: 5px; }
}

/* lists & tables */
.list-head { display: flex; flex-direction: column; gap: 10px; }
.list-tools { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.list-tools input[type="text"], .list-tools input:not([type]) { flex: 1; min-width: 160px; padding: 8px 11px; border: 1px solid #d1d5db; border-radius: 8px; outline: none; }
.list-tools input:focus { border-color: #6b7280; }
.toggle { display: inline-flex; align-items: center; gap: 6px; padding: 7px 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; font-weight: 650; cursor: pointer; }
.toggle input { margin: 0; }
.table-wrap { overflow-x: auto; margin-top: 14px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eef1f5; }
th { background: #f8fafc; font-weight: 750; color: #374151; white-space: nowrap; }
tbody tr:hover { background: #fafbfc; }
.row-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.stock-low { color: #b42318; font-weight: 700; }
.raw { margin-top: 16px; }
.raw summary { cursor: pointer; font-weight: 700; }
.raw pre { margin-top: 8px; padding: 12px; background: #111827; color: #d1d5db; border-radius: 10px; overflow: auto; font-size: 12px; }

/* till bar */
.till-bar { margin-top: 18px; padding: 12px; border: 1px dashed #d1d5db; border-radius: 10px; background: #f8fafc; }
.till-bar-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.till-bar-row span { font-size: 13px; color: #374151; font-weight: 650; }
.till-bar-row input { flex: 1; min-width: 120px; padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; }

/* toast */
.toast { position: fixed; top: 16px; right: 16px; z-index: 50; padding: 11px 14px; border-radius: 10px; font-size: 13px; font-weight: 650; box-shadow: 0 8px 24px rgba(17,24,39,0.15); max-width: 400px; }
.toast-ok { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; }
.toast-err { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }

/* modal */
.modal-backdrop { position: fixed; inset: 0; background: rgba(17, 24, 39, 0.5); z-index: 100; display: flex; align-items: flex-start; justify-content: center; padding: 20px; overflow: auto; }
.modal { width: 100%; max-width: 520px; background: #fff; border-radius: 14px; box-shadow: 0 20px 60px rgba(17,24,39,0.25); margin: 40px 0; }
.modal.wide { max-width: 760px; }
.modal-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.modal-head h3 { margin: 0; font-size: 16px; letter-spacing: -0.01em; }
.modal-body { padding: 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

/* stock summary in modal */
.stock-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 10px; background: #f8fafc; }
.stock-summary strong { display: block; margin-top: 4px; font-size: 20px; }
.stock-summary strong.neg { color: #b42318; }

/* segmented control */
.segmented { display: inline-flex; border: 1px solid #d1d5db; border-radius: 8px; overflow: hidden; }
.segmented button { padding: 8px 14px; border: 0; background: #fff; font-size: 13px; font-weight: 650; color: #374151; }
.segmented button.on { background: #111827; color: #fff; }

/* form errors */
.form-error { padding: 10px 12px; border: 1px solid #fecaca; background: #fef2f2; color: #991b1b; border-radius: 8px; font-size: 13px; }

/* responsive */
@media (min-width: 640px) {
  .topbar { flex-direction: row; align-items: center; justify-content: space-between; padding: 20px 30px; }
  .topbar-right { flex-direction: row; align-items: center; }
  .api-control input { width: 240px; }
  .content { padding: 22px; }
  .card { padding: 22px; }
  .stat-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .pos { grid-template-columns: 1.2fr 1fr; }
  .list-head { flex-direction: row; align-items: flex-end; justify-content: space-between; }
  .form-grid { grid-template-columns: 1fr 1fr; }
}
@media (min-width: 900px) {
  .layout { flex-direction: row; }
  .sidebar { width: 230px; flex: 0 0 230px; border-right: 1px solid #e5e7eb; border-bottom: 0; min-height: calc(100vh - 90px); }
  .navigation { flex-direction: column; overflow: visible; padding: 12px; }
  .nav { width: 100%; }
  .sidebar-foot { display: block; }
  .content { padding: 28px; }
}
`;