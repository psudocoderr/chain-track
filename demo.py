"""
demo.py — Runs a full end-to-end demo of the supply chain entirely from the CLI.

Simulates:
  1. Register Manufacturer, Distributor, Retailer, Customer
  2. Manufacturer creates two products
  3. Transfers to Distributor → Retailer
  4. Delivery confirmed at each step
  5. Retailer sells to Customer
  6. Print full provenance / history for each product

Usage:
    python demo.py
"""

from supply_chain import SupplyChainManager, ROLES, STATUSES
from datetime import datetime


def separator(title=""):
    width = 60
    if title:
        pad = (width - len(title) - 2) // 2
        print("\n" + "─" * pad + f" {title} " + "─" * pad)
    else:
        print("\n" + "─" * width)


def print_product(sc, pid):
    p = sc.get_product(pid)
    print(f"  Product #{p['id']}: {p['name']}")
    print(f"    Description : {p['description']}")
    print(f"    Status      : {p['status_icon']} {p['status']}")
    print(f"    Price       : {p['price_eth']} ETH")
    print(f"    Owner       : {p['current_owner']}")
    print(f"    Created     : {p['created_at']}")


def print_history(sc, pid):
    history = sc.get_product_history(pid)
    print(f"\n  📋 Provenance Trail for Product #{pid}:")
    for i, e in enumerate(history):
        print(f"\n  [{i+1}] {e['timestamp']}")
        print(f"      Actor  : {e['role_icon']} {e['actor_name']} ({e['actor_role']})")
        print(f"      Status : {e['status_icon']} {e['status']}")
        print(f"      Location: {e['location']}")
        if e["notes"]:
            print(f"      Notes  : {e['notes']}")


def main():
    print("=" * 60)
    print("  ChainTrack — Blockchain Supply Chain Demo")
    print("=" * 60)

    sc = SupplyChainManager()
    accounts = sc.accounts

    # ── Step 1: Register participants ──────────────────────────────────────
    separator("1. REGISTERING PARTICIPANTS")

    participants = {
        "manufacturer": (accounts[1], "FreshFoods Ltd.",   0),
        "distributor":  (accounts[2], "SwiftLogistics Co.", 1),
        "retailer":     (accounts[3], "QuickMart Retail",   2),
        "customer":     (accounts[4], "Rahul Sharma",        3),
    }

    for role_key, (addr, name, role_id) in participants.items():
        result = sc.register_participant(addr, name, role_id)
        print(f"  ✅ Registered: {name} as {ROLES[role_id]}")
        print(f"     Address: {addr}")

    # ── Step 2: Create products ────────────────────────────────────────────
    separator("2. CREATING PRODUCTS")

    mfr_addr = participants["manufacturer"][0]

    r1 = sc.create_product(
        mfr_addr,
        name="Organic Basmati Rice 5kg",
        description="Premium quality organic basmati rice, pesticide-free",
        price_eth=0.02,
        location="FreshFoods Factory, Dehradun",
        notes="Batch #BR2024-001, QC passed, organic certified"
    )
    pid1 = r1["product_id"]
    print(f"  ✅ Created Product #{pid1}: Organic Basmati Rice 5kg")

    r2 = sc.create_product(
        mfr_addr,
        name="Cold-Pressed Coconut Oil 1L",
        description="100% pure virgin coconut oil, cold-pressed",
        price_eth=0.015,
        location="FreshFoods Factory, Dehradun",
        notes="Batch #CO2024-007, export quality"
    )
    pid2 = r2["product_id"]
    print(f"  ✅ Created Product #{pid2}: Cold-Pressed Coconut Oil 1L")

    # ── Step 3: Manufacturer → Distributor ────────────────────────────────
    separator("3. MANUFACTURER → DISTRIBUTOR")

    dist_addr = participants["distributor"][0]

    sc.transfer_ownership(
        mfr_addr, pid1, dist_addr,
        location="SwiftLogistics Depot, New Delhi",
        notes="Shipped via refrigerated truck. Invoice #INV-2024-789"
    )
    print(f"  ✅ Product #{pid1} transferred to Distributor")

    sc.transfer_ownership(
        mfr_addr, pid2, dist_addr,
        location="SwiftLogistics Depot, New Delhi",
        notes="Shipped via standard cargo. Fragile handling required."
    )
    print(f"  ✅ Product #{pid2} transferred to Distributor")

    # ── Step 4: Distributor confirms receipt ───────────────────────────────
    separator("4. DISTRIBUTOR CONFIRMS RECEIPT")

    sc.confirm_delivery(
        dist_addr, pid1,
        location="SwiftLogistics Depot, New Delhi",
        notes="Package received intact. Temperature maintained at 18°C."
    )
    print(f"  ✅ Product #{pid1} delivery confirmed by Distributor")

    sc.confirm_delivery(
        dist_addr, pid2,
        location="SwiftLogistics Depot, New Delhi",
        notes="Package received. 5 units. No damage."
    )
    print(f"  ✅ Product #{pid2} delivery confirmed by Distributor")

    # ── Step 5: Distributor → Retailer ────────────────────────────────────
    separator("5. DISTRIBUTOR → RETAILER")

    ret_addr = participants["retailer"][0]

    sc.transfer_ownership(
        dist_addr, pid1, ret_addr,
        location="QuickMart Warehouse, Bangalore",
        notes="Last-mile delivery complete. Ready for shelf stocking."
    )
    print(f"  ✅ Product #{pid1} transferred to Retailer")

    sc.transfer_ownership(
        dist_addr, pid2, ret_addr,
        location="QuickMart Warehouse, Bangalore",
        notes="Dispatched with cold-chain maintenance."
    )
    print(f"  ✅ Product #{pid2} transferred to Retailer")

    # ── Step 6: Retailer confirms receipt ─────────────────────────────────
    separator("6. RETAILER CONFIRMS RECEIPT")

    sc.confirm_delivery(
        ret_addr, pid1,
        location="QuickMart Store, Indiranagar, Bangalore",
        notes="Stocked on shelf. Expiry date checked."
    )
    print(f"  ✅ Product #{pid1} received and stocked by Retailer")

    sc.confirm_delivery(
        ret_addr, pid2,
        location="QuickMart Store, Indiranagar, Bangalore",
        notes="Stocked on shelf."
    )
    print(f"  ✅ Product #{pid2} received and stocked by Retailer")

    # ── Step 7: Sell to Customer ───────────────────────────────────────────
    separator("7. RETAILER SELLS TO CUSTOMER")

    cust_addr = participants["customer"][0]

    sc.sell_to_customer(
        ret_addr, pid1, cust_addr,
        location="QuickMart Store, Indiranagar, Bangalore",
        notes="POS Sale #5521. Customer verified product authenticity via QR."
    )
    print(f"  ✅ Product #{pid1} sold to Customer: Rahul Sharma")

    # ── Step 8: Print final state ──────────────────────────────────────────
    separator("8. FINAL PRODUCT STATUS")

    for pid in [pid1, pid2]:
        print_product(sc, pid)
        print()

    # ── Step 9: Full provenance trail ─────────────────────────────────────
    separator("9. FULL PROVENANCE TRAIL")

    for pid in [pid1, pid2]:
        print_history(sc, pid)
        print()

    # ── Summary ───────────────────────────────────────────────────────────
    separator("SUMMARY")
    stats = sc.get_stats()
    print(f"  Total products on-chain : {stats['total_products']}")
    for status, count in stats['by_status'].items():
        print(f"  {status:15s}        : {count}")

    print("\n  🎉 Demo complete! All transactions recorded immutably on-chain.")
    print("     Run `python app.py` and open http://localhost:5000 for the dashboard.\n")


if __name__ == "__main__":
    main()
