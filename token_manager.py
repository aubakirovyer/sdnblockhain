#!/usr/bin/env python3

import re
import json
from web3 import Web3, HTTPProvider
from visualize import FloodlightVisualizer

"""
token_manager.py

1. Builds the network topology from Floodlight using FloodlightVisualizer.
2. Extracts the host nodes and (optionally) their IP or MAC addresses.
3. Connects to Ganache via Web3.py.
4. Mints tokens (e.g., 1000 each) for those hosts on a simple 'MyToken' contract.

Requirements:
 - Ganache running on port 8545
 - A deployed MyToken contract (address + ABI in build/contracts/MyToken.json)
 - 'visualizer.py' in same folder with the FloodlightVisualizer class
"""

def main():
    # 1) Build the network topology from Floodlight
    fv = FloodlightVisualizer()
    fv.build_topology()

    # 2) Collect the hosts from the Graph
    #    In your code, each host node label is like "h10.0.0.1" or "h00:00:00:00:00:01"
    #    We'll store them in a list
    host_labels = []
    for node, data in fv.topology.nodes(data=True):
        if data.get("type") == "host":
            host_labels.append(node)  # e.g. "h10.0.0.1"

    print("Discovered host labels:", host_labels)
    # For demonstration, let's extract something from these labels
    # e.g. if the label starts with 'h10.', treat it as an IP, else fallback to MAC
    # In a real system, you might store these addresses differently.

    # 3) Connect to Ganache
    w3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("[Error] Could not connect to Ganache at 127.0.0.1:8545. Is it running?")
        return

    # 4) Load MyToken contract info (ABI + address)
    #    Make sure you have previously run `truffle compile && truffle migrate`
    try:
        with open("sdn-blockchain/build/contracts/MyToken.json") as f:
            contract_json = json.load(f)
    except FileNotFoundError:
        print("[Error] Could not find build/contracts/MyToken.json - compile your contract first.")
        return

    abi = contract_json["abi"]
    # The 'networks' field in MyToken.json might have the deployed address if using Truffle
    # Otherwise, set it manually to the address from 'truffle migrate'
    # Example: contract_address = "0x1234abcd..."
    # We'll attempt to parse from "networks" if it exists:
    networks_info = contract_json.get("networks", {})
    if not networks_info:
        print("[Warning] No 'networks' info found, fallback to manual address.")
        contract_address = "0x0000000000000000000000000000000000000000"
    else:
        # Get the first network entry
        # Alternatively, you can look up your specific network id
        # e.g. if Ganache uses network_id=5777
        network_id = list(networks_info.keys())[0]  # e.g. "5777"
        contract_address = networks_info[network_id]["address"]

    print("Using contract address:", contract_address)
    contract = w3.eth.contract(address=contract_address, abi=abi)

    # 5) Use one of Ganache’s default accounts to pay for gas
    #    If Ganache CLI gave us private keys, we can pick the first one.
    #    Or if you use Ganache UI, you can copy a private key from the UI
    #    For demonstration, place your private key here:
    ganache_private_key = "0xABC123YOURKEY..."  # <-- replace with actual key

    # Create a local 'Account' instance
    acct = w3.eth.account.from_key(ganache_private_key)
    w3.eth.default_account = acct.address

    # 6) For each host, let's produce an ephemeral "host address" (or real key)
    #    Then mint tokens to it. We'll do 1000 tokens per host.
    #    Realistically, each host would manage its own key, but this is a quick demo.
    #    We'll store them in a dictionary for reference
    host_addresses = {}
    for label in host_labels:
        # If label is like "h10.0.0.1", let's create an address
        new_acct = w3.eth.account.create(label)  # seed with the label (just for reproducibility)
        host_addresses[label] = new_acct.address

    # 7) Mint tokens to each host’s address
    for label, host_addr in host_addresses.items():
        # Build the transaction
        tx = contract.functions.mint(host_addr, 1000).build_transaction({
            'from': acct.address,
            'nonce': w3.eth.get_transaction_count(acct.address),
            'gas': 300000,
            'gasPrice': w3.toWei('1', 'gwei'),
        })
        # Sign and send
        signed_tx = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[Minted] 1000 tokens for {label} at {host_addr} in block {receipt.blockNumber} gasUsed={receipt.gasUsed}")

    # 8) Show final balances
    for label, host_addr in host_addresses.items():
        bal = contract.functions.balanceOf(host_addr).call()
        print(f"{label} => {host_addr} has {bal} tokens")


if __name__ == "__main__":
    main()
