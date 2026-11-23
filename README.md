# ⛓ ChainValve — Blockchain Supply Chain + ESP32 Smart Solenoid Valve

> Ethereum smart contracts + ESP32 smart solenoid valve controlled by blockchain events.
> Every delivery confirmation triggers the valve in real time.

---

## 🗂 Project Structure

```
supply-chain-demo/
│
├── contracts/
│   └── SupplyChain.sol          # Solidity smart contract
│
├── build/                       # Auto-generated after deploy.py
│   ├── SupplyChain_abi.json
│   └── contract_address.txt
│
├── templates/
│   └── index.html               # Web dashboard UI
│
├── deploy.py                    # Compiles & deploys the contract
├── supply_chain.py              # Python wrapper (calls valve on delivery)
├── app.py                       # Flask REST API + dashboard
├── demo.py                      # CLI end-to-end simulation
├── valve.py                     # ESP32 smart valve controller
├── esp32_solenoid.ino           # Arduino firmware for ESP32
├── requirements.txt
└── README.md
```

---

## ⚡ How It Works

```
[Browser / CLI]
      │
      ▼
[Flask / demo.py]  ──── web3.py ────▶  [Ganache GUI]
      │                                      │
      │                             [SupplyChain.sol]
      │                              confirmDelivery()
      │                              sellToCustomer()
      │
      └──── HTTP GET /open ─────▶  [ESP32 Smart Solenoid Valve]
                                    Built-in LED ON = Valve OPEN
```

### What the ESP32 represents

The ESP32 is a **Smart Solenoid Valve** — a valve with embedded intelligence:
WiFi connectivity, an HTTP server, and the ability to receive commands
directly from the blockchain network via Flask.

| LED State | Valve State | Meaning |
|-----------|-------------|---------|
| OFF | CLOSED | Shipment not yet verified on-chain |
| 🔆 ON | OPEN | Blockchain confirmed delivery — valve released |

### Valve triggers automatically on:

| Action | Valve |
|--------|-------|
| `confirmDelivery()` — Distributor or Retailer confirms receipt | 🔆 Opens |
| `sellToCustomer()` — Retailer sells to Customer | 🔆 Opens |

---

## 🚀 How to Run

### Step 1 — Start Ganache GUI

Open Ganache → click **Quickstart** → confirm it is running on port **7545**. Leave it open.

---

### Step 2 — Flash the ESP32

1. Open `esp32_solenoid.ino` in **Arduino IDE**
2. Update WiFi credentials at the top of the file:
   ```cpp
   const char* WIFI_SSID     = "YOUR_WIFI_NAME";
   const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
   ```
3. Upload to ESP32
4. Open **Serial Monitor** at **115200 baud**
5. Copy the IP address it prints, for example:
   ```
   [WiFi] IP Address: 192.168.1.105
   ```

---

### Step 3 — Set the ESP32 IP

Open `valve.py` and update line 13:
```python
ESP32_IP = "http://192.168.1.105"   # ← paste your IP here
```

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Deploy the Smart Contract

```bash
python deploy.py
```

This will:
- Install the Solidity compiler (first run only)
- Compile `SupplyChain.sol`
- Deploy to your local Ganache chain
- Save the ABI and contract address to `build/` automatically

> ✅ Run this **once only**. Re-running creates a new contract instance.

---

### Step 6 — Run the Project

**Option A — Web Dashboard** *(recommended for demo)*

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

**Option B — Terminal Demo** *(faster to show)*

```bash
python demo.py
```

Runs the full Manufacturer → Distributor → Retailer → Customer flow automatically
and prints every step with the valve triggering live.

---

## 📋 Quick Reference — Run Order

```
1. Ganache GUI      →  Quickstart (port 7545)
2. ESP32            →  Flash firmware + copy IP
3. valve.py         →  Paste IP
4. pip install      →  requirements.txt
5. deploy.py        →  Once only
6. app.py / demo.py →  Run the project
```

---

## 🔍 Smart Contract — Supply Chain Flow

```
🏭 Manufacturer  →  🚚 Distributor  →  🏪 Retailer  →  👤 Customer
   createProduct()   transferOwnership() confirmDelivery()  sellToCustomer()
                      confirmDelivery()  transferOwnership()
                                              🔆 VALVE OPENS at confirmDelivery + sellToCustomer
```

### Roles

| Role | Permissions |
|------|-------------|
| Manufacturer | Create products, transfer to Distributor |
| Distributor | Confirm receipt, transfer to Retailer |
| Retailer | Confirm receipt, sell to Customer |
| Customer | Final owner |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `deploy.py` fails | Make sure Ganache GUI is open and on port 7545 |
| Valve LED does not turn on | Check IP in `valve.py`; ESP32 and laptop must be on same WiFi |
| `Cannot connect to Ganache` | Ganache must be running before `app.py` or `demo.py` |
| `build/` folder missing | Run `deploy.py` first |
| ESP32 shows no IP in Serial Monitor | Check WiFi credentials in `.ino` file |

---

## 📦 Requirements

| Tool | Details |
|------|---------|
| Python | 3.10+ |
| Ganache GUI | Running on port 7545 |
| Arduino IDE | With ESP32 board support installed |
| ESP32 | Any variant (ESP32-WROOM etc.) — **no other hardware needed** |
