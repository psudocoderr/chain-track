"""
valve.py — ESP32 Solenoid Valve Controller
===========================================
Drop this file next to supply_chain.py.
Update ESP32_IP below, then it's ready.

Called automatically on:
  - confirmDelivery()  → valve opens (product arrived)
  - sellToCustomer()   → valve opens (product dispensed)
"""

import requests

ESP32_IP    = "http://192.168.0.164"   # ← paste your ESP32's IP here
TIMEOUT_SEC = 3


def open_valve():
    """Open the solenoid valve via ESP32."""
    try:
        r = requests.get(f"{ESP32_IP}/open", timeout=TIMEOUT_SEC)
        print(f"🔓 [VALVE] Opened — ESP32 replied: {r.json().get('message','ok')}")
    except Exception as e:
        print(f"⚠️  [VALVE] ESP32 unreachable ({e}). Continuing without valve.")


def close_valve():
    """Close the solenoid valve via ESP32."""
    try:
        r = requests.get(f"{ESP32_IP}/close", timeout=TIMEOUT_SEC)
        print(f"🔒 [VALVE] Closed — ESP32 replied: {r.json().get('message','ok')}")
    except Exception as e:
        print(f"⚠️  [VALVE] ESP32 unreachable ({e}). Continuing without valve.")


def valve_status() -> str:
    """Return 'open', 'closed', or 'unknown'."""
    try:
        r = requests.get(f"{ESP32_IP}/status", timeout=TIMEOUT_SEC)
        return r.json().get("valve", "unknown")
    except Exception:
        return "unknown"
