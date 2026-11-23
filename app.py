"""
app.py — Flask web server exposing a REST API + dashboard for ChainTrack.

Run:
    python app.py

Then open http://localhost:5000 in your browser.
"""

from flask import Flask, jsonify, request, render_template_string
from supply_chain import SupplyChainManager, ROLES

app = Flask(__name__)
sc  = None   # Lazy-loaded on first request


def get_sc() -> SupplyChainManager:
    global sc
    if sc is None:
        sc = SupplyChainManager()
    return sc


# ── REST API ──────────────────────────────────────────────────────────────────

@app.route("/api/accounts")
def api_accounts():
    return jsonify(get_sc().get_all_accounts_with_info())


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    result = get_sc().register_participant(data["address"], data["name"], int(data["role"]))
    return jsonify(result)


@app.route("/api/products")
def api_products():
    return jsonify(get_sc().get_all_products())


@app.route("/api/products/<int:product_id>")
def api_product(product_id):
    return jsonify(get_sc().get_product(product_id))


@app.route("/api/products/<int:product_id>/history")
def api_history(product_id):
    return jsonify(get_sc().get_product_history(product_id))


@app.route("/api/products/create", methods=["POST"])
def api_create():
    data   = request.json
    result = get_sc().create_product(
        data["from_address"], data["name"], data["description"],
        float(data["price_eth"]), data["location"], data.get("notes", "")
    )
    return jsonify(result)


@app.route("/api/products/transfer", methods=["POST"])
def api_transfer():
    data = request.json
    result = get_sc().transfer_ownership(
        data["from_address"], int(data["product_id"]),
        data["to_address"], data["location"], data.get("notes", "")
    )
    return jsonify(result)


@app.route("/api/products/confirm_delivery", methods=["POST"])
def api_confirm():
    data = request.json
    result = get_sc().confirm_delivery(
        data["from_address"], int(data["product_id"]),
        data["location"], data.get("notes", "")
    )
    return jsonify(result)


@app.route("/api/products/sell", methods=["POST"])
def api_sell():
    data = request.json
    result = get_sc().sell_to_customer(
        data["from_address"], int(data["product_id"]),
        data["customer_address"], data["location"], data.get("notes", "")
    )
    return jsonify(result)


@app.route("/api/stats")
def api_stats():
    return jsonify(get_sc().get_stats())


# ── Dashboard (served at "/") ─────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ChainTrack — Blockchain Supply Chain</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600;800&display=swap" rel="stylesheet"/>
<style>
  :root {
    --bg:       #0d0f14;
    --surface:  #161b25;
    --border:   #252d3d;
    --accent:   #00e5ff;
    --accent2:  #a78bfa;
    --green:    #10b981;
    --yellow:   #f59e0b;
    --red:      #ef4444;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --font-mono: 'Space Mono', monospace;
    --font-sans: 'DM Sans', sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font-sans); min-height: 100vh; }

  /* ── Layout ── */
  header { padding: 1.25rem 2rem; display: flex; align-items: center; gap: 1rem;
           border-bottom: 1px solid var(--border); background: var(--surface); }
  header .logo { font-family: var(--font-mono); font-size: 1.4rem; color: var(--accent);
                 letter-spacing: -0.5px; }
  header .logo span { color: var(--accent2); }
  header .subtitle { color: var(--muted); font-size: 0.85rem; }
  header .badge { margin-left: auto; background: #0a2a1a; border: 1px solid var(--green);
                  color: var(--green); padding: .25rem .75rem; border-radius: 99px;
                  font-size: .78rem; font-family: var(--font-mono); }

  nav { display: flex; gap: .25rem; padding: 1rem 2rem; border-bottom: 1px solid var(--border); }
  nav button { background: none; border: 1px solid transparent; color: var(--muted);
               padding: .5rem 1rem; border-radius: 8px; cursor: pointer;
               font-family: var(--font-sans); font-size: .9rem; transition: all .2s; }
  nav button.active, nav button:hover { border-color: var(--border); color: var(--text); background: var(--surface); }
  nav button.active { color: var(--accent); border-color: var(--accent); }

  main { padding: 2rem; max-width: 1200px; margin: 0 auto; }
  .tab { display: none; }
  .tab.active { display: block; }

  /* ── Cards ── */
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
          padding: 1.5rem; margin-bottom: 1.5rem; }
  .card-title { font-weight: 800; font-size: 1rem; margin-bottom: 1.25rem;
                color: var(--accent); text-transform: uppercase; letter-spacing: 1px; font-size: .8rem; }

  /* ── Stats row ── */
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
               padding: 1.25rem; text-align: center; }
  .stat-value { font-family: var(--font-mono); font-size: 2rem; font-weight: 700; color: var(--accent); }
  .stat-label { font-size: .78rem; color: var(--muted); margin-top: .25rem; text-transform: uppercase; letter-spacing: .5px; }

  /* ── Table ── */
  table { width: 100%; border-collapse: collapse; font-size: .875rem; }
  th { text-align: left; padding: .75rem 1rem; color: var(--muted); font-weight: 600;
       border-bottom: 1px solid var(--border); font-size: .75rem; text-transform: uppercase; letter-spacing: .5px; }
  td { padding: .75rem 1rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.02); }

  /* ── Status badges ── */
  .badge-status { padding: .2rem .6rem; border-radius: 99px; font-size: .72rem;
                  font-family: var(--font-mono); font-weight: 700; }
  .badge-Created    { background: #1e293b; color: #94a3b8; }
  .badge-InTransit  { background: #1c1a08; color: var(--yellow); }
  .badge-Delivered  { background: #0a2a1a; color: var(--green); }
  .badge-Sold       { background: #2a1a2a; color: var(--accent2); }

  .role-badge { padding: .15rem .5rem; border-radius: 6px; font-size: .72rem; font-weight: 600; }
  .role-Manufacturer { background: #0d2233; color: #38bdf8; }
  .role-Distributor  { background: #1c1a08; color: var(--yellow); }
  .role-Retailer     { background: #0a2a1a; color: var(--green); }
  .role-Customer     { background: #2a1a2a; color: var(--accent2); }

  /* ── Forms ── */
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .form-group { display: flex; flex-direction: column; gap: .4rem; }
  .form-group label { font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
  .form-group input, .form-group select, .form-group textarea {
    background: var(--bg); border: 1px solid var(--border); border-radius: 8px;
    color: var(--text); padding: .65rem .9rem; font-family: var(--font-sans); font-size: .9rem;
    transition: border .2s; }
  .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
    outline: none; border-color: var(--accent); }
  .form-group select option { background: var(--surface); }

  .btn { padding: .65rem 1.4rem; border-radius: 8px; font-family: var(--font-sans); font-weight: 600;
         font-size: .9rem; cursor: pointer; border: none; transition: all .2s; }
  .btn-primary { background: var(--accent); color: #000; }
  .btn-primary:hover { opacity: .85; transform: translateY(-1px); }
  .btn-outline { background: none; border: 1px solid var(--border); color: var(--text); }
  .btn-outline:hover { border-color: var(--accent); color: var(--accent); }

  .btn-row { margin-top: 1.25rem; display: flex; gap: .75rem; align-items: center; }

  /* ── Toast ── */
  #toast { position: fixed; bottom: 2rem; right: 2rem; padding: .85rem 1.4rem; border-radius: 10px;
           font-size: .9rem; z-index: 999; transform: translateY(100px); opacity: 0;
           transition: all .3s; max-width: 360px; }
  #toast.show { transform: translateY(0); opacity: 1; }
  #toast.success { background: #0a2a1a; border: 1px solid var(--green); color: var(--green); }
  #toast.error   { background: #2a0a0a; border: 1px solid var(--red);   color: var(--red); }

  /* ── History timeline ── */
  .timeline { position: relative; padding-left: 1.5rem; }
  .timeline::before { content: ''; position: absolute; left: .5rem; top: 0; bottom: 0;
                       width: 2px; background: var(--border); }
  .timeline-item { position: relative; margin-bottom: 1.25rem; }
  .timeline-item::before { content: ''; position: absolute; left: -1.15rem; top: .4rem;
                            width: 10px; height: 10px; border-radius: 50%;
                            background: var(--accent); border: 2px solid var(--bg); }
  .timeline-header { font-weight: 600; font-size: .9rem; }
  .timeline-meta { font-size: .78rem; color: var(--muted); margin-top: .2rem; }
  .timeline-notes { font-size: .82rem; color: var(--text); margin-top: .4rem;
                    padding: .4rem .75rem; background: rgba(255,255,255,.03);
                    border-left: 2px solid var(--border); border-radius: 4px; }

  .addr { font-family: var(--font-mono); font-size: .72rem; color: var(--muted); }

  .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
  .section-title  { font-size: 1.2rem; font-weight: 800; }

  /* ── Chain visual ── */
  .chain-viz { display: flex; align-items: center; gap: .5rem; padding: 1rem 0; overflow-x: auto; }
  .chain-node { text-align: center; min-width: 120px; }
  .chain-node .icon { width: 48px; height: 48px; border-radius: 12px; display: flex;
                      align-items: center; justify-content: center; font-size: 1.5rem;
                      margin: 0 auto .4rem; }
  .chain-node .label { font-size: .78rem; font-weight: 600; }
  .chain-node .sublabel { font-size: .68rem; color: var(--muted); }
  .chain-arrow { font-size: 1.2rem; color: var(--border); flex-shrink: 0; }
  .chain-node.active .icon { box-shadow: 0 0 0 2px var(--accent); }

  @media (max-width: 700px) {
    .stats-row { grid-template-columns: 1fr 1fr; }
    .form-grid  { grid-template-columns: 1fr; }
    main { padding: 1rem; }
  }
</style>
</head>
<body>

<header>
  <div>
    <div class="logo">Chain<span>Track</span></div>
    <div class="subtitle">Blockchain Supply Chain on Ethereum</div>
  </div>
  <div class="badge" id="conn-badge">⬤ Connecting…</div>
  <button id="seed-btn" onclick="seedDemoData()"
    style="margin-left:.75rem;padding:.35rem 1rem;border-radius:8px;font-size:.8rem;
           font-family:var(--font-sans);font-weight:600;cursor:pointer;
           background:none;border:1px solid var(--accent2);color:var(--accent2);
           transition:all .2s">
    🌱 Load Demo Data
  </button>
</header>

<nav>
  <button class="active" onclick="showTab('dashboard')">📊 Dashboard</button>
  <button onclick="showTab('products')">📦 Products</button>
  <button onclick="showTab('actions')">⚡ Actions</button>
  <button onclick="showTab('participants')">👥 Participants</button>
</nav>

<main>

  <!-- ── Dashboard Tab ── -->
  <div id="tab-dashboard" class="tab active">
    <div class="stats-row" id="stats-row">
      <div class="stat-card"><div class="stat-value" id="stat-total">—</div><div class="stat-label">Total Products</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-intransit" style="color:var(--yellow)">—</div><div class="stat-label">In Transit</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-delivered" style="color:var(--green)">—</div><div class="stat-label">Delivered</div></div>
      <div class="stat-card"><div class="stat-value" id="stat-sold" style="color:var(--accent2)">—</div><div class="stat-label">Sold</div></div>
    </div>

    <div class="card">
      <div class="card-title">Supply Chain Flow</div>
      <div class="chain-viz">
        <div class="chain-node"><div class="icon" style="background:#0d2233">🏭</div><div class="label">Manufacturer</div><div class="sublabel">Creates product</div></div>
        <div class="chain-arrow">→</div>
        <div class="chain-node"><div class="icon" style="background:#1c1a08">🚚</div><div class="label">Distributor</div><div class="sublabel">Ships goods</div></div>
        <div class="chain-arrow">→</div>
        <div class="chain-node"><div class="icon" style="background:#0a2a1a">🏪</div><div class="label">Retailer</div><div class="sublabel">Receives & sells</div></div>
        <div class="chain-arrow">→</div>
        <div class="chain-node"><div class="icon" style="background:#2a1a2a">👤</div><div class="label">Customer</div><div class="sublabel">Final buyer</div></div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Recent Products</div>
      <table id="dash-table">
        <thead><tr><th>ID</th><th>Name</th><th>Status</th><th>Price</th><th>Created</th></tr></thead>
        <tbody id="dash-tbody"><tr><td colspan="5" style="color:var(--muted);text-align:center">Loading…</td></tr></tbody>
      </table>
    </div>
  </div>

  <!-- ── Products Tab ── -->
  <div id="tab-products" class="tab">
    <div class="section-header">
      <div class="section-title">All Products</div>
      <button class="btn btn-outline" onclick="loadProducts()">↻ Refresh</button>
    </div>
    <div class="card">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Description</th><th>Status</th><th>Price (ETH)</th><th>Owner</th><th>History</th></tr></thead>
        <tbody id="products-tbody"><tr><td colspan="7" style="color:var(--muted);text-align:center">Loading…</td></tr></tbody>
      </table>
    </div>
    <!-- History panel -->
    <div class="card" id="history-panel" style="display:none">
      <div class="card-title" id="history-title">Product History</div>
      <div class="timeline" id="history-timeline"></div>
    </div>
  </div>

  <!-- ── Actions Tab ── -->
  <div id="tab-actions" class="tab">

    <!-- Create Product -->
    <div class="card">
      <div class="card-title">🆕 Create Product (Manufacturer)</div>
      <div class="form-grid">
        <div class="form-group"><label>Manufacturer Address</label>
          <select id="create-from" ></select></div>
        <div class="form-group"><label>Product Name</label>
          <input id="create-name" type="text" placeholder="e.g. Organic Rice 5kg"/></div>
        <div class="form-group"><label>Description</label>
          <input id="create-desc" type="text" placeholder="Brief description"/></div>
        <div class="form-group"><label>Price (ETH)</label>
          <input id="create-price" type="number" step="0.001" value="0.01"/></div>
        <div class="form-group"><label>Origin Location</label>
          <input id="create-loc" type="text" placeholder="e.g. Mumbai Factory"/></div>
        <div class="form-group"><label>Notes</label>
          <input id="create-notes" type="text" placeholder="Batch #, QC passed, etc."/></div>
      </div>
      <div class="btn-row"><button class="btn btn-primary" onclick="createProduct()">Create Product</button></div>
    </div>

    <!-- Transfer Ownership -->
    <div class="card">
      <div class="card-title">🚚 Transfer Ownership</div>
      <div class="form-grid">
        <div class="form-group"><label>From (Current Owner)</label>
          <select id="transfer-from"></select></div>
        <div class="form-group"><label>To (Next Party)</label>
          <select id="transfer-to"></select></div>
        <div class="form-group"><label>Product ID</label>
          <input id="transfer-pid" type="number" min="1"/></div>
        <div class="form-group"><label>Current Location</label>
          <input id="transfer-loc" type="text" placeholder="e.g. Delhi Warehouse"/></div>
        <div class="form-group"><label>Notes</label>
          <input id="transfer-notes" type="text" placeholder="Shipment details…"/></div>
      </div>
      <div class="btn-row"><button class="btn btn-primary" onclick="transferOwnership()">Transfer</button></div>
    </div>

    <!-- Confirm Delivery -->
    <div class="card">
      <div class="card-title">✅ Confirm Delivery (Distributor / Retailer)</div>
      <div class="form-grid">
        <div class="form-group"><label>Current Owner Address</label>
          <select id="confirm-from"></select></div>
        <div class="form-group"><label>Product ID</label>
          <input id="confirm-pid" type="number" min="1"/></div>
        <div class="form-group"><label>Delivery Location</label>
          <input id="confirm-loc" type="text" placeholder="e.g. Retailer Store, Bangalore"/></div>
        <div class="form-group"><label>Notes</label>
          <input id="confirm-notes" type="text" placeholder="Condition on arrival…"/></div>
      </div>
      <div class="btn-row"><button class="btn btn-primary" onclick="confirmDelivery()">Confirm Delivery</button></div>
    </div>

    <!-- Sell to Customer -->
    <div class="card">
      <div class="card-title">💰 Sell to Customer (Retailer)</div>
      <div class="form-grid">
        <div class="form-group"><label>Retailer Address</label>
          <select id="sell-from"></select></div>
        <div class="form-group"><label>Customer Address</label>
          <select id="sell-to"></select></div>
        <div class="form-group"><label>Product ID</label>
          <input id="sell-pid" type="number" min="1"/></div>
        <div class="form-group"><label>Store Location</label>
          <input id="sell-loc" type="text" placeholder="e.g. Mumbai Retail Store"/></div>
      </div>
      <div class="btn-row"><button class="btn btn-primary" onclick="sellToCustomer()">Sell</button></div>
    </div>
  </div>

  <!-- ── Participants Tab ── -->
  <div id="tab-participants" class="tab">
    <div class="section-header">
      <div class="section-title">Participants</div>
    </div>

    <div class="card">
      <div class="card-title">➕ Register Participant</div>
      <div class="form-grid">
        <div class="form-group"><label>Wallet Address</label>
          <select id="reg-addr"></select></div>
        <div class="form-group"><label>Name</label>
          <input id="reg-name" type="text" placeholder="Company / Person name"/></div>
        <div class="form-group"><label>Role</label>
          <select id="reg-role">
            <option value="0">🏭 Manufacturer</option>
            <option value="1">🚚 Distributor</option>
            <option value="2">🏪 Retailer</option>
            <option value="3">👤 Customer</option>
          </select></div>
      </div>
      <div class="btn-row"><button class="btn btn-primary" onclick="registerParticipant()">Register</button></div>
    </div>

    <div class="card">
      <div class="card-title">Registered Accounts</div>
      <table>
        <thead><tr><th>Address</th><th>Name</th><th>Role</th><th>Balance</th></tr></thead>
        <tbody id="participants-tbody"><tr><td colspan="4" style="color:var(--muted);text-align:center">Loading…</td></tr></tbody>
      </table>
    </div>
  </div>

</main>

<div id="toast"></div>

<script>
const API = '';

// ── Utilities ──────────────────────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}

function toast(msg, type='success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show ' + type;
  setTimeout(() => el.className = '', 3500);
}

async function api(path, opts={}) {
  const r = await fetch(API + path, opts);
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || JSON.stringify(d));
  return d;
}

function statusBadge(s) {
  const cls = s.replace(' ','');
  return `<span class="badge-status badge-${cls}">${s}</span>`;
}
function roleBadge(r) {
  return `<span class="role-badge role-${r}">${r}</span>`;
}
function shortAddr(a) {
  return a ? `${a.slice(0,6)}…${a.slice(-4)}` : '—';
}

// ── Load & populate selects ───────────────────────────────────────────────
let allAccounts = [];

async function loadAccounts() {
  allAccounts = await api('/api/accounts');
  const selects = ['create-from','transfer-from','transfer-to','confirm-from',
                   'sell-from','sell-to','reg-addr'];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    allAccounts.forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.address;
      const reg = a.is_registered ? `[${a.role}] ${a.name}` : '[Unregistered]';
      opt.textContent = `${shortAddr(a.address)} — ${reg}`;
      el.appendChild(opt);
    });
  });
}

async function loadParticipants() {
  const tbody = document.getElementById('participants-tbody');
  tbody.innerHTML = allAccounts.map(a => `
    <tr>
      <td class="addr">${a.address}</td>
      <td>${a.is_registered ? a.name : '<span style="color:var(--muted)">—</span>'}</td>
      <td>${a.is_registered ? roleBadge(a.role) : ''}</td>
      <td style="font-family:var(--font-mono);font-size:.82rem">${a.balance} ETH</td>
    </tr>`).join('');
}

async function loadProducts() {
  const products = await api('/api/products');
  const tbody = document.getElementById('products-tbody');
  if (!products.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="color:var(--muted);text-align:center">No products yet. Create one in Actions.</td></tr>';
    return;
  }
  tbody.innerHTML = products.map(p => `
    <tr>
      <td style="font-family:var(--font-mono)">#${p.id}</td>
      <td>${p.name}</td>
      <td style="color:var(--muted);font-size:.82rem">${p.description}</td>
      <td>${statusBadge(p.status)}</td>
      <td style="font-family:var(--font-mono);font-size:.82rem">${p.price_eth} ETH</td>
      <td class="addr">${shortAddr(p.current_owner)}</td>
      <td><button class="btn btn-outline" style="padding:.3rem .7rem;font-size:.78rem"
          onclick="showHistory(${p.id},'${p.name}')">History</button></td>
    </tr>`).join('');
}

async function loadStats() {
  const stats = await api('/api/stats');
  document.getElementById('stat-total').textContent     = stats.total_products;
  document.getElementById('stat-intransit').textContent = stats.by_status['In Transit'] || 0;
  document.getElementById('stat-delivered').textContent = stats.by_status['Delivered']  || 0;
  document.getElementById('stat-sold').textContent      = stats.by_status['Sold']       || 0;

  // dashboard table — last 5
  const products = await api('/api/products');
  const tbody = document.getElementById('dash-tbody');
  if (!products.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="color:var(--muted);text-align:center">No products yet.</td></tr>';
    return;
  }
  tbody.innerHTML = products.slice(-5).reverse().map(p => `
    <tr>
      <td style="font-family:var(--font-mono)">#${p.id}</td>
      <td>${p.name}</td>
      <td>${statusBadge(p.status)}</td>
      <td style="font-family:var(--font-mono);font-size:.82rem">${p.price_eth} ETH</td>
      <td style="color:var(--muted);font-size:.82rem">${p.created_at}</td>
    </tr>`).join('');
}

async function showHistory(pid, name) {
  const history = await api(`/api/products/${pid}/history`);
  const panel   = document.getElementById('history-panel');
  const tl      = document.getElementById('history-timeline');
  document.getElementById('history-title').textContent = `📦 Product #${pid} — ${name} — History`;
  tl.innerHTML = history.map(e => `
    <div class="timeline-item">
      <div class="timeline-header">${e.role_icon} ${e.actor_name} <span style="font-weight:400;color:var(--muted)">·</span> ${statusBadge(e.status)}</div>
      <div class="timeline-meta">${e.timestamp} · 📍 ${e.location}</div>
      ${e.notes ? `<div class="timeline-notes">${e.notes}</div>` : ''}
      <div class="addr" style="margin-top:.25rem">${e.actor}</div>
    </div>`).join('');
  panel.style.display = 'block';
  panel.scrollIntoView({behavior:'smooth'});
}

// ── Actions ───────────────────────────────────────────────────────────────
async function registerParticipant() {
  try {
    const r = await api('/api/register', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        address: document.getElementById('reg-addr').value,
        name:    document.getElementById('reg-name').value,
        role:    document.getElementById('reg-role').value,
      })
    });
    toast(`✅ Registered ${r.name} as ${r.role}`);
    await loadAccounts();
    await loadParticipants();
  } catch(e) { toast('❌ ' + e.message, 'error'); }
}

async function createProduct() {
  try {
    const r = await api('/api/products/create', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        from_address: document.getElementById('create-from').value,
        name:         document.getElementById('create-name').value,
        description:  document.getElementById('create-desc').value,
        price_eth:    document.getElementById('create-price').value,
        location:     document.getElementById('create-loc').value,
        notes:        document.getElementById('create-notes').value,
      })
    });
    toast(`✅ Product #${r.product_id} created!`);
    await loadStats();
  } catch(e) { toast('❌ ' + e.message, 'error'); }
}

async function transferOwnership() {
  try {
    await api('/api/products/transfer', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        from_address: document.getElementById('transfer-from').value,
        to_address:   document.getElementById('transfer-to').value,
        product_id:   document.getElementById('transfer-pid').value,
        location:     document.getElementById('transfer-loc').value,
        notes:        document.getElementById('transfer-notes').value,
      })
    });
    toast('✅ Ownership transferred successfully');
    await loadStats();
  } catch(e) { toast('❌ ' + e.message, 'error'); }
}

async function confirmDelivery() {
  try {
    await api('/api/products/confirm_delivery', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        from_address: document.getElementById('confirm-from').value,
        product_id:   document.getElementById('confirm-pid').value,
        location:     document.getElementById('confirm-loc').value,
        notes:        document.getElementById('confirm-notes').value,
      })
    });
    toast('✅ Delivery confirmed on-chain');
    await loadStats();
  } catch(e) { toast('❌ ' + e.message, 'error'); }
}

async function sellToCustomer() {
  try {
    await api('/api/products/sell', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        from_address:     document.getElementById('sell-from').value,
        customer_address: document.getElementById('sell-to').value,
        product_id:       document.getElementById('sell-pid').value,
        location:         document.getElementById('sell-loc').value,
        notes:            '',
      })
    });
    toast('✅ Product sold to customer!');
    await loadStats();
  } catch(e) { toast('❌ ' + e.message, 'error'); }
}

// ── Seed Demo Data ────────────────────────────────────────────────────────
async function seedDemoData() {
  const btn = document.getElementById('seed-btn');
  btn.textContent = '⏳ Loading…';
  btn.disabled = true;
  try {
    const r = await fetch('/api/seed', {method:'POST'});
    const d = await r.json();
    if (d.success) {
      toast('✅ ' + d.message);
      btn.textContent = '✓ Demo Data Loaded';
      btn.style.color = 'var(--green)';
      btn.style.borderColor = 'var(--green)';
      await loadAccounts();
      await loadStats();
      await loadProducts();
      await loadParticipants();
    } else {
      toast('ℹ️ ' + d.message);
      btn.textContent = '✓ Already Loaded';
      btn.style.color = 'var(--muted)';
      btn.style.borderColor = 'var(--muted)';
    }
  } catch(e) {
    toast('❌ Seed failed: ' + e.message, 'error');
    btn.textContent = '🌱 Load Demo Data';
    btn.disabled = false;
  }
}

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  try {
    await loadAccounts();
    await loadStats();
    await loadProducts();
    await loadParticipants();
    document.getElementById('conn-badge').textContent = '⬤ Connected';
    document.getElementById('conn-badge').style.color = 'var(--green)';
    document.getElementById('conn-badge').style.borderColor = 'var(--green)';
    document.getElementById('conn-badge').style.background = '#0a2a1a';
  } catch(e) {
    document.getElementById('conn-badge').textContent = '⬤ Disconnected';
    document.getElementById('conn-badge').style.color = 'var(--red)';
  }
}

init();
</script>
</body>
</html>"""


@app.route("/api/seed", methods=["POST"])
def api_seed():
    """
    Pre-populate the blockchain with demo participants and products.
    Safe to call only once — skips if products already exist.
    """
    sc = get_sc()

    # Guard — don't double-seed
    if sc.get_stats()["total_products"] > 0:
        return jsonify({"success": False, "message": "Demo data already loaded."})

    accounts = sc.accounts

    # ── 1. Register participants ──────────────────────────────
    sc.register_participant(accounts[1], "FreshFoods Ltd.",    0)  # Manufacturer
    sc.register_participant(accounts[2], "SwiftLogistics Co.", 1)  # Distributor
    sc.register_participant(accounts[3], "QuickMart Retail",   2)  # Retailer
    sc.register_participant(accounts[4], "Rahul Sharma",       3)  # Customer

    # ── 2. Product 1 — already In Transit (Distributor has it) ──
    r1 = sc.create_product(
        accounts[1],
        name="Organic Basmati Rice 5kg",
        description="Premium organic basmati, pesticide-free, certified",
        price_eth=0.02,
        location="FreshFoods Factory, Dehradun",
        notes="Batch #BR2024-001, QC passed"
    )
    pid1 = r1["product_id"]
    sc.transfer_ownership(
        accounts[1], pid1, accounts[2],
        location="SwiftLogistics Depot, New Delhi",
        notes="Shipped via refrigerated truck. Invoice #INV-2024-789"
    )

    # ── 3. Product 2 — freshly Created, ready to demo full flow ──
    sc.create_product(
        accounts[1],
        name="Cold-Pressed Coconut Oil 1L",
        description="100% pure virgin coconut oil, cold-pressed, export quality",
        price_eth=0.015,
        location="FreshFoods Factory, Dehradun",
        notes="Batch #CO2024-007, ready for dispatch"
    )

    return jsonify({
        "success": True,
        "message": "Demo data loaded! 4 participants registered, 2 products created.",
        "details": {
            "participants": ["FreshFoods Ltd.", "SwiftLogistics Co.", "QuickMart Retail", "Rahul Sharma"],
            "products": [
                {"id": pid1, "name": "Organic Basmati Rice 5kg",   "state": "In Transit"},
                {"id": 2,    "name": "Cold-Pressed Coconut Oil 1L", "state": "Created"},
            ]
        }
    })


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


if __name__ == "__main__":
    print("🚀 ChainTrack starting at http://localhost:5000")
    print("   Make sure Ganache is running and you've run deploy.py first.\n")
    app.run(debug=True, port=5000)
