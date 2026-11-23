"""
deploy.py — Compiles and deploys the SupplyChain smart contract to a local Ganache instance.

Usage:
    python deploy.py

Requirements:
    pip install web3 py-solc-x
"""

import json
import os
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3


# ── Config ────────────────────────────────────────────────────────────────────
GANACHE_URL     = "http://127.0.0.1:7545"   # Default Ganache GUI port
SOLIDITY_FILE   = Path(__file__).parent / "contracts" / "SupplyChain.sol"
ABI_OUTPUT      = Path(__file__).parent / "build" / "SupplyChain_abi.json"
ADDRESS_OUTPUT  = Path(__file__).parent / "build" / "contract_address.txt"
SOLC_VERSION    = "0.8.19"


def compile_contract() -> tuple[list, str]:
    """Compile the Solidity contract and return (abi, bytecode)."""
    print(f"[1/3] Installing solc {SOLC_VERSION}...")
    install_solc(SOLC_VERSION)

    source = SOLIDITY_FILE.read_text()

    print("[2/3] Compiling SupplyChain.sol...")
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"SupplyChain.sol": {"content": source}},
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                },
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]}
                }
            },
        },
        solc_version=SOLC_VERSION,
    )

    contract_data = compiled["contracts"]["SupplyChain.sol"]["SupplyChain"]
    abi      = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    return abi, bytecode


def deploy(abi: list, bytecode: str) -> str:
    """Deploy the compiled contract and return its address."""
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise ConnectionError(
            f"Cannot connect to Ganache at {GANACHE_URL}. "
            "Make sure Ganache is running."
        )

    deployer = w3.eth.accounts[0]
    w3.eth.default_account = deployer

    print(f"[3/3] Deploying from account: {deployer}")
    print(f"      Balance: {w3.from_wei(w3.eth.get_balance(deployer), 'ether'):.4f} ETH")

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash  = Contract.constructor().transact({"from": deployer, "gas": 3_000_000})
    receipt  = w3.eth.wait_for_transaction_receipt(tx_hash)

    address = receipt["contractAddress"]
    print(f"\n✅ Contract deployed at: {address}")
    print(f"   Gas used: {receipt['gasUsed']:,}")
    return address


def save_artifacts(abi: list, address: str) -> None:
    """Persist ABI and address so other scripts can load them."""
    ABI_OUTPUT.parent.mkdir(exist_ok=True)
    ABI_OUTPUT.write_text(json.dumps(abi, indent=2))
    ADDRESS_OUTPUT.write_text(address)
    print(f"\n📁 ABI saved to:     {ABI_OUTPUT}")
    print(f"📁 Address saved to: {ADDRESS_OUTPUT}")


if __name__ == "__main__":
    abi, bytecode = compile_contract()
    address       = deploy(abi, bytecode)
    save_artifacts(abi, address)
    print("\n🎉 Deployment complete. Run `python app.py` to start the dashboard.")
