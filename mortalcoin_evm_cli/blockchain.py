"""
Blockchain interaction module for MortalCoin EVM CLI.

This module provides functions for interacting with the MortalCoin smart contract
on the Ethereum blockchain.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt, Wei


def load_abi() -> Dict[str, Any]:
    """Load the ABI from the abi.json file."""
    # Try to load from the package directory first
    package_abi_path = Path(__file__).parent / "abi.json"
    if package_abi_path.exists():
        with open(package_abi_path, "r") as f:
            return json.load(f)
    
    # Fall back to the parent directory
    parent_abi_path = Path(__file__).parent.parent / "abi.json"
    if parent_abi_path.exists():
        with open(parent_abi_path, "r") as f:
            return json.load(f)
    
    raise FileNotFoundError("ABI file not found in package or parent directory")


def get_web3_connection(rpc_url: str) -> Web3:
    """
    Establish a connection to the Ethereum blockchain.
    
    Args:
        rpc_url: The URL of the Ethereum RPC endpoint.
        
    Returns:
        A Web3 instance connected to the specified RPC endpoint.
    """
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to Ethereum node at {rpc_url}")
    return web3


def get_contract(web3: Web3, contract_address: str) -> Contract:
    """
    Get a contract instance for the specified address.
    
    Args:
        web3: A Web3 instance.
        contract_address: The address of the contract.
        
    Returns:
        A Contract instance.
    """
    abi = load_abi()
    return web3.eth.contract(address=contract_address, abi=abi)


def create_game(
    web3: Web3,
    contract: Contract,
    private_key: str,
    bet_amount: int,
    pool_address: str
) -> Tuple[str, int]:
    """
    Create a new game on the blockchain.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        private_key: The private key of the user.
        bet_amount: The bet amount in wei.
        pool_address: The address of the pool.
        
    Returns:
        A tuple containing the transaction hash and the game ID.
    """
    # Get the account from the private key
    account = web3.eth.account.from_key(private_key)
    address = account.address
    
    # Get the nonce for the account
    nonce = web3.eth.get_transaction_count(address)
    
    # Estimate gas for the transaction
    gas_estimate = contract.functions.createGame(pool_address).estimate_gas({
        'from': address,
        'value': bet_amount,
        'nonce': nonce,
    })
    
    # Try to use EIP-1559 transaction format
    try:
        # Get the max priority fee (tip for miners)
        max_priority_fee = web3.eth.max_priority_fee
        
        # Get the latest block to extract the base fee
        latest_block = web3.eth.get_block('latest')
        
        # Check if the block has a base fee (EIP-1559 support)
        if hasattr(latest_block, 'baseFeePerGas') and latest_block.baseFeePerGas is not None:
            base_fee = latest_block.baseFeePerGas
            
            # Calculate max fee per gas (base fee + priority fee with buffer)
            # Adding 2x priority fee as buffer to account for base fee increases
            max_fee_per_gas = base_fee + (max_priority_fee * 2)
            
            # Build the transaction using EIP-1559 format
            transaction = contract.functions.createGame(pool_address).build_transaction({
                'from': address,
                'value': bet_amount,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'maxFeePerGas': max_fee_per_gas,
                'maxPriorityFeePerGas': max_priority_fee,
                'nonce': nonce,
                'type': 2,  # Explicitly set transaction type to EIP-1559
            })
            print("Using EIP-1559 transaction format")
        else:
            # Fallback to legacy transaction if baseFeePerGas is not available
            raise AttributeError("Latest block does not have baseFeePerGas")
    except Exception as e:
        print(f"Warning: Could not use EIP-1559 transaction format: {e}")
        print("Falling back to legacy transaction format")
        
        # Build the transaction using legacy format
        transaction = contract.functions.createGame(pool_address).build_transaction({
            'from': address,
            'value': bet_amount,
            'gas': int(gas_estimate * 1.2),  # Add 20% buffer
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce,
        })
    
    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    
    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    # Wait for the transaction to be mined
    print(f"Transaction sent: {tx_hash.hex()}")
    print("Waiting for transaction to be mined...")
    
    receipt = wait_for_transaction_receipt(web3, tx_hash.hex())
    
    # Get the game ID from the transaction receipt
    # The createGame function returns the game ID, which should be in the logs
    # We need to decode the logs to get the return value
    game_id = None
    
    # Try to get the game ID from the return value
    try:
        # Get the current game ID (it should be the last created game)
        game_id = contract.functions.currentGameId().call() - 1
    except Exception as e:
        print(f"Failed to get game ID: {e}")
        # As a fallback, we can try to get it from the logs
        # This would require knowing the event signature and parsing the logs
        # For simplicity, we'll just return None for now
    
    return tx_hash.hex(), game_id


def wait_for_transaction_receipt(
    web3: Web3, 
    tx_hash: str, 
    timeout: int = 120, 
    poll_interval: float = 0.1
) -> TxReceipt:
    """
    Wait for a transaction receipt to be available.
    
    Args:
        web3: A Web3 instance.
        tx_hash: The transaction hash.
        timeout: The maximum time to wait in seconds.
        poll_interval: The interval between polls in seconds.
        
    Returns:
        The transaction receipt.
        
    Raises:
        TimeoutError: If the transaction receipt is not available within the timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt is not None:
                if receipt["status"] == 1:
                    print(f"Transaction successful! Gas used: {receipt['gasUsed']}")
                else:
                    print(f"Transaction failed! Gas used: {receipt['gasUsed']}")
                return receipt
        except TransactionNotFound:
            pass
        
        # Print a progress indicator
        if int((time.time() - start_time) / 5) % 2 == 0:
            print(".", end="", flush=True)
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Transaction not mined within {timeout} seconds")


def get_game_info(web3: Web3, contract: Contract, game_id: int) -> Dict[str, Any]:
    """
    Get information about a game.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The ID of the game.
        
    Returns:
        A dictionary containing information about the game.
    """
    # Call the games getter function
    game_info = contract.functions.games(game_id).call()
    
    # Convert the result to a dictionary
    # The games function returns a tuple with the following elements:
    # (betAmount, player1, gameEndTimestamp, player1Pool, player2, player2Pool, state, player1Position, player2Position, player1Pnl, player2Pnl)
    return {
        "betAmount": game_info[0],
        "player1": game_info[1],
        "gameEndTimestamp": game_info[2],
        "player1Pool": game_info[3],
        "player2": game_info[4],
        "player2Pool": game_info[5],
        "state": game_info[6],
        "player1Position": {
            "openingPrice": game_info[7][0],
            "hashedDirection": game_info[7][1].hex(),
            "state": game_info[7][2]
        },
        "player2Position": {
            "openingPrice": game_info[8][0],
            "hashedDirection": game_info[8][1].hex(),
            "state": game_info[8][2]
        },
        "player1Pnl": game_info[9],
        "player2Pnl": game_info[10]
    }