"""
supply_chain.py — Python wrapper around the SupplyChain smart contract.

Provides a clean SupplyChainManager class used by both app.py and the CLI.
"""

import json
from pathlib import Path
from datetime import datetime
from web3 import Web3
from valve import open_valve   # ← valve integration

# ── Paths ─────────────────────────────────────────────────────────────────────
BUILD_DIR       = Path(__file__).parent / "build"
ABI_PATH        = BUILD_DIR / "SupplyChain_abi.json"
ADDRESS_PATH    = BUILD_DIR / "contract_address.txt"

GANACHE_URL     = "http://127.0.0.1:7545"

# Role / Status mappings (mirror Solidity enums)
ROLES    = {0: "Manufacturer", 1: "Distributor", 2: "Retailer", 3: "Customer"}
STATUSES = {0: "Created", 1: "In Transit", 2: "Delivered", 3: "Sold"}

ROLE_ICONS   = {"Manufacturer": "🏭", "Distributor": "🚚", "Retailer": "🏪", "Customer": "👤"}
STATUS_ICONS = {"Created": "🆕", "In Transit": "📦", "Delivered": "✅", "Sold": "💰"}


class SupplyChainManager:
    """High-level interface to the SupplyChain contract."""

    def __init__(self, ganache_url: str = GANACHE_URL):
        self.w3 = Web3(Web3.HTTPProvider(ganache_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to Ganache at {ganache_url}")

        abi     = json.loads(ABI_PATH.read_text())
        address = ADDRESS_PATH.read_text().strip()

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi,
        )
        self.accounts = self.w3.eth.accounts
        self.admin    = self.accounts[0]

    # ── Participants ──────────────────────────────────────────────────────────

    def register_participant(self, address: str, name: str, role: int) -> dict:
        """Register a participant. role: 0=Manufacturer, 1=Distributor, 2=Retailer, 3=Customer"""
        address = Web3.to_checksum_address(address)
        tx = self.contract.functions.registerParticipant(address, name, role).transact(
            {"from": self.admin, "gas": 200_000}
        )
        self.w3.eth.wait_for_transaction_receipt(tx)
        return {"success": True, "address": address, "name": name, "role": ROLES[role]}

    def get_participant(self, address: str) -> dict:
        address = Web3.to_checksum_address(address)
        p = self.contract.functions.getParticipant(address).call()
        return {
            "address":       p[0],
            "name":          p[1],
            "role":          ROLES[p[2]],
            "role_id":       p[2],
            "is_registered": p[3],
            "icon":          ROLE_ICONS.get(ROLES[p[2]], "❓"),
        }

    def get_all_accounts_with_info(self) -> list[dict]:
        """Return all Ganache accounts with their registration status."""
        result = []
        for acc in self.accounts:
            info = self.get_participant(acc)
            balance = self.w3.from_wei(self.w3.eth.get_balance(acc), "ether")
            info["balance"] = float(f"{balance:.4f}")
            result.append(info)
        return result

    # ── Products ──────────────────────────────────────────────────────────────

    def create_product(self, from_address: str, name: str, description: str,
                       price_eth: float, location: str, notes: str = "") -> dict:
        price_wei = self.w3.to_wei(price_eth, "ether")
        from_address = Web3.to_checksum_address(from_address)
        tx = self.contract.functions.createProduct(
            name, description, price_wei, location, notes
        ).transact({"from": from_address, "gas": 3_000_000})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)

        # Extract product ID from the ProductCreated event
        logs = self.contract.events.ProductCreated().process_receipt(receipt)
        product_id = logs[0]["args"]["productId"] if logs else None
        return {"success": True, "product_id": product_id, "tx_hash": receipt["transactionHash"].hex()}

    def get_product(self, product_id: int) -> dict:
        p = self.contract.functions.getProduct(product_id).call()
        return {
            "id":           p[0],
            "name":         p[1],
            "description":  p[2],
            "manufacturer": p[3],
            "current_owner": p[4],
            "status":       STATUSES[p[5]],
            "status_id":    p[5],
            "created_at":   datetime.fromtimestamp(p[6]).strftime("%Y-%m-%d %H:%M:%S"),
            "price_eth":    float(self.w3.from_wei(p[7], "ether")),
            "status_icon":  STATUS_ICONS.get(STATUSES[p[5]], ""),
        }

    def get_all_products(self) -> list[dict]:
        ids = self.contract.functions.getAllProductIds().call()
        return [self.get_product(i) for i in ids]

    def get_product_history(self, product_id: int) -> list[dict]:
        events = self.contract.functions.getProductHistory(product_id).call()
        history = []
        for e in events:
            history.append({
                "actor":      e[0],
                "actor_name": e[1],
                "actor_role": ROLES[e[2]],
                "status":     STATUSES[e[3]],
                "location":   e[4],
                "timestamp":  datetime.fromtimestamp(e[5]).strftime("%Y-%m-%d %H:%M:%S"),
                "notes":      e[6],
                "role_icon":  ROLE_ICONS.get(ROLES[e[2]], ""),
                "status_icon": STATUS_ICONS.get(STATUSES[e[3]], ""),
            })
        return history

    # ── Transfer Actions ──────────────────────────────────────────────────────

    def transfer_ownership(self, from_address: str, product_id: int,
                           to_address: str, location: str, notes: str = "") -> dict:
        from_address = Web3.to_checksum_address(from_address)
        to_address   = Web3.to_checksum_address(to_address)
        tx = self.contract.functions.transferOwnership(
            product_id, to_address, location, notes
        ).transact({"from": from_address, "gas": 300_000})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return {"success": True, "tx_hash": receipt["transactionHash"].hex()}

    def confirm_delivery(self, from_address: str, product_id: int,
                         location: str, notes: str = "") -> dict:
        from_address = Web3.to_checksum_address(from_address)
        tx = self.contract.functions.confirmDelivery(
            product_id, location, notes
        ).transact({"from": from_address, "gas": 300_000})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        open_valve()   # ← product physically arrives → valve opens
        return {"success": True, "tx_hash": receipt["transactionHash"].hex()}

    def sell_to_customer(self, from_address: str, product_id: int,
                         customer_address: str, location: str, notes: str = "") -> dict:
        from_address      = Web3.to_checksum_address(from_address)
        customer_address  = Web3.to_checksum_address(customer_address)
        tx = self.contract.functions.sellToCustomer(
            product_id, customer_address, location, notes
        ).transact({"from": from_address, "gas": 300_000})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        open_valve()   # ← product dispensed to customer → valve opens
        return {"success": True, "tx_hash": receipt["transactionHash"].hex()}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        products = self.get_all_products()
        total    = len(products)
        by_status = {"Created": 0, "In Transit": 0, "Delivered": 0, "Sold": 0}
        for p in products:
            by_status[p["status"]] = by_status.get(p["status"], 0) + 1
        return {"total_products": total, "by_status": by_status}
