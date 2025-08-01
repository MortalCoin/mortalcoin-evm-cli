"""
Blockchain interaction module for MortalCoin EVM CLI.

This module provides functions for interacting with the MortalCoin smart contract
on the Ethereum blockchain.
"""

import json
import time
from enum import IntEnum
from pathlib import Path
from typing import Dict, Any, Tuple, Callable

from eth_abi import encode
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt, Wei


class Direction(IntEnum):
    """
    Enum representing the direction of a position.
    
    Attributes:
        Long: Long position (0)
        Short: Short position (1)
    """
    Long = 0
    Short = 1


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
    bet_amount: Wei,
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
    # Prepare transaction parameters
    tx_params = {
        'value': bet_amount
    }
    
    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.createGame(pool_address),
        private_key=private_key,
        tx_params=tx_params
    )
    
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
    
    return tx_hash, game_id


def build_sign_send_transaction(
    web3: Web3,
    contract_function: Callable,
    private_key: str,
    tx_params: Dict[str, Any]
) -> Tuple[str, TxReceipt]:
    """
    Build, sign, and send a transaction for a contract function call.
    
    Args:
        web3: A Web3 instance.
        contract_function: The contract function to call.
        private_key: The private key to sign the transaction with.
        tx_params: Transaction parameters (from, value, etc.).
        
    Returns:
        A tuple containing the transaction hash (hex string) and the transaction receipt.
    """
    # Get the account from the private key
    account = web3.eth.account.from_key(private_key)
    address = account.address
    
    # Ensure 'from' address is set correctly
    tx_params['from'] = address
    
    # Get the nonce if not provided
    if 'nonce' not in tx_params:
        tx_params['nonce'] = web3.eth.get_transaction_count(address)
    
    # Estimate gas if not provided
    if 'gas' not in tx_params:
        gas_estimate = contract_function.estimate_gas(tx_params)
        tx_params['gas'] = int(gas_estimate * 1.2)  # Add 20% buffer
    
    # Try to use EIP-1559 transaction format
    try:
        # Get the max priority fee (tip for miners)
        max_priority_fee = web3.eth.max_priority_fee
        
        # Get the latest block to extract the base fee
        latest_block = web3.eth.get_block('latest')
        
        # Get the chain ID
        chain_id = web3.eth.chain_id
        
        # Check if the block has a base fee (EIP-1559 support)
        if hasattr(latest_block, 'baseFeePerGas') and latest_block.baseFeePerGas is not None:
            base_fee = latest_block.baseFeePerGas
            
            # Calculate max fee per gas (base fee + priority fee with buffer)
            # Adding 2x priority fee as buffer to account for base fee increases
            max_fee_per_gas = base_fee + (max_priority_fee * 2)
            
            # Build the transaction using EIP-1559 format
            eip1559_params = tx_params.copy()
            eip1559_params.update({
                'maxFeePerGas': max_fee_per_gas,
                'maxPriorityFeePerGas': max_priority_fee,
                'type': 2,  # Explicitly set transaction type to EIP-1559
                'chainId': chain_id,  # Add chain ID to prevent replay attacks
            })
            
            transaction = contract_function.build_transaction(eip1559_params)
            print("Using EIP-1559 transaction format")
        else:
            # Fallback to legacy transaction if baseFeePerGas is not available
            raise AttributeError("Latest block does not have baseFeePerGas")
    except Exception as e:
        print(f"Warning: Could not use EIP-1559 transaction format: {e}")
        print("Falling back to legacy transaction format")
        
        # Get the chain ID if not already retrieved
        if 'chain_id' not in locals():
            chain_id = web3.eth.chain_id
            
        # Build the transaction using legacy format
        legacy_params = tx_params.copy()
        if 'gasPrice' not in legacy_params:
            legacy_params['gasPrice'] = web3.eth.gas_price
        legacy_params['chainId'] = chain_id  # Add chain ID to prevent replay attacks
        
        transaction = contract_function.build_transaction(legacy_params)
    
    # Sign the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    
    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_hash_hex = tx_hash.hex()
    
    # Wait for the transaction to be mined
    print(f"Transaction sent: {tx_hash_hex}")
    print("Waiting for transaction to be mined...")
    
    receipt = wait_for_transaction_receipt(web3, tx_hash_hex)
    
    return tx_hash_hex, receipt


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


def join_game(
    web3: Web3,
    contract: Contract,
    game_id: int,
    player1_private_key: str,
    player2_private_key: str,
    player2_pool: str,
    bet_amount: Wei
) -> Tuple[str, Dict[str, Any]]:
    """
    Join an existing game on the blockchain.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The ID of the game to join.
        player1_private_key: The private key of player1 who created the game.
        player2_private_key: The private key of player2 who is joining the game.
        player2_pool: The address of player2's pool.
        bet_amount: The bet amount in wei (must match the game's bet amount).
        
    Returns:
        A tuple containing the transaction hash and the updated game info.
    """
    # Get accounts from private keys
    player1_account = web3.eth.account.from_key(player1_private_key)
    player2_account = web3.eth.account.from_key(player2_private_key)
    
    player1_address = player1_account.address
    player2_address = player2_account.address
    
    # Convert pool address to checksum format
    player2_pool = Web3.to_checksum_address(player2_pool)
    
    # Set signature expiration (current time + 1 hour)
    signature_expiration = int(time.time()) + 3600
    
    # Create the EIP-712 typed data for the signature
    # This matches the structure in the contract's joinGame function
    domain_type_dict = {
        "name": "MortalCoin",
        "version": "1",
        "chainId": web3.eth.chain_id,
        "verifyingContract": contract.address
    }
    
    # Define the JoinGame type for EIP-712
    join_game_type = {
        "JoinGame": [
            {"name": "gameId", "type": "uint256"},
            {"name": "player2", "type": "address"},
            {"name": "signatureExpiration", "type": "uint256"}
        ]
    }
    
    # Create the message to sign
    message = {
        "gameId": game_id,
        "player2": player2_address,
        "signatureExpiration": signature_expiration
    }
    
    # Sign the message with player1's private key
    player1_signature = player1_account.sign_typed_data(
        domain_type_dict,
        join_game_type,
        message
    ).signature
    
    # Prepare transaction parameters
    tx_params = {
        'from': player2_address,
        'value': bet_amount
    }
    
    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.joinGame(
            game_id,
            player2_pool,
            signature_expiration,
            player1_signature
        ),
        private_key=player2_private_key,
        tx_params=tx_params
    )
    
    # Get the updated game info
    game_info = get_game_info(web3, contract, game_id)
    
    return tx_hash, game_info


def validate_create_game_transaction(
    web3: Web3,
    contract: Contract,
    game_id: int,
    tx_hash: str,
    pool_address: str
) -> Dict[str, Any]:
    """
    Validate a transaction that created a game.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The expected game ID.
        tx_hash: The transaction hash.
        pool_address: The expected pool address.
        
    Returns:
        A dictionary containing validation results.
    
    Raises:
        TransactionNotFound: If the transaction is not found.
        ValueError: If the transaction validation fails.
    """
    # Convert addresses to checksum format
    pool_address = Web3.to_checksum_address(pool_address)
    
    # Check if the transaction exists and is confirmed
    try:
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise ValueError("Transaction is not confirmed")
    except TransactionNotFound:
        raise ValueError("Transaction not found")
    
    # Check if the transaction was successful
    if tx_receipt["status"] != 1:
        raise ValueError("Transaction execution failed")
    
    # Get the transaction details
    tx = web3.eth.get_transaction(tx_hash)
    
    # Check if the transaction was sent to the contract address
    if tx["to"].lower() != contract.address.lower():
        raise ValueError(f"Transaction was not sent to the contract address {contract.address}")
    
    # Decode the transaction input data
    try:
        # Get the function signature for createGame
        # Calculate the function signature (first 4 bytes of keccak hash of 'createGame(address)')
        # Function signature should be exactly 4 bytes (8 hex characters)
        create_game_signature = web3.keccak(text='createGame(address)').hex()[:8]
        
        # Check if the transaction called the createGame function
        # Convert create_game_signature to bytes for comparison with tx["input"] which is in bytes format
        create_game_signature_bytes = bytes.fromhex(create_game_signature)
        
        if not tx["input"].startswith(create_game_signature_bytes):
            raise ValueError("Transaction did not call createGame function")
        
        # Decode the function parameters
        decoded_input = contract.decode_function_input(tx["input"])
        
        # Check if the pool address matches
        if decoded_input[1]["pool"].lower() != pool_address.lower():
            raise ValueError(f"Transaction called createGame with pool address {decoded_input[1]['pool']} instead of {pool_address}")
    except Exception as e:
        raise ValueError(f"Failed to decode transaction input: {e}")
    
    # Check if the game exists and has the expected ID
    try:
        # Get the game info
        game_info = get_game_info(web3, contract, game_id)
        
        # Check if the game was created by this transaction
        if game_info["player1Pool"].lower() != pool_address.lower():
            raise ValueError(f"Game {game_id} has pool address {game_info['player1Pool']} instead of {pool_address}")
    except Exception as e:
        raise ValueError(f"Failed to verify game ID: {e}")
    
    # All validations passed
    return {
        "confirmed": True,
        "successful": True,
        "called_create_game": True,
        "pool_address_match": True,
        "game_id_valid": True,
        "game_info": game_info
    }


def post_position(
    web3: Web3,
    contract: Contract,
    player_private_key: str,
    backend_private_key: str,
    game_id: int,
    direction: Direction,
    nonce: int
) -> str:
    """
    Post a position on the blockchain.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        player_private_key: The private key of the player.
        backend_private_key: The private key of the backend.
        game_id: The ID of the game.
        direction: The direction of the position (Long or Short).
        nonce: A random nonce for the position.
        
    Returns:
        The transaction hash.
    """
    # Get accounts from private keys
    player_account = web3.eth.account.from_key(player_private_key)
    backend_account = web3.eth.account.from_key(backend_private_key)
    
    player_address = player_account.address

    # Calculate the hashed direction
    # In Solidity: keccak256(abi.encode(gameId, direction, nonce))
    encoded_data = encode(['uint256', 'uint8', 'uint256'], [game_id, direction, nonce])
    hashed_direction = web3.keccak(encoded_data)

    # Create the EIP-712 typed data for the backend signature
    domain_type_dict = {
        "name": "MortalCoin",
        "version": "1",
        "chainId": web3.eth.chain_id,
        "verifyingContract": contract.address
    }
    
    # Define the PostPosition type for EIP-712
    post_position_type = {
        "PostPosition": [
            {"name": "gameId", "type": "uint256"},
            {"name": "player", "type": "address"},
            {"name": "hashedDirection", "type": "bytes32"}
        ]
    }

    # Create the message to sign
    message = {
        "gameId": game_id,
        "player": player_address,
        "hashedDirection": hashed_direction
    }
    
    # Sign the message with backend's private key
    backend_signature = backend_account.sign_typed_data(
        domain_type_dict,
        post_position_type,
        message
    ).signature
    
    # Prepare transaction parameters
    tx_params = {
        'from': player_address
    }

    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.postPosition(
            game_id,
            hashed_direction,
            backend_signature
        ),
        private_key=player_private_key,
        tx_params=tx_params
    )
    
    return tx_hash


def close_position(
    web3: Web3,
    contract: Contract,
    private_key: str,
    game_id: int,
    direction: Direction,
    nonce: int
) -> str:
    """
    Close a position on the blockchain.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        private_key: The private key of the player.
        game_id: The ID of the game.
        direction: The direction of the position (Long or Short).
        nonce: The nonce used when posting the position.
        
    Returns:
        The transaction hash.
    """
    # Get account from private key
    account = web3.eth.account.from_key(private_key)
    player_address = account.address
    
    # Prepare transaction parameters
    tx_params = {
        'from': player_address
    }
    
    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.closePosition(
            game_id,
            direction,
            nonce
        ),
        private_key=private_key,
        tx_params=tx_params
    )
    
    return tx_hash


def finish_game(
    web3: Web3,
    contract: Contract,
    private_key: str,
    game_id: int,
    direction: Direction,
    nonce: int
) -> str:
    """
    Finish a game on the blockchain by calling the finishGame function.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        private_key: The private key of the player.
        game_id: The ID of the game.
        direction: The direction of the position (Long or Short).
        nonce: The nonce used when posting the position.
        
    Returns:
        The transaction hash.
    """
    # Get account from private key
    account = web3.eth.account.from_key(private_key)
    player_address = account.address
    
    # Prepare transaction parameters
    tx_params = {
        'from': player_address
    }
    
    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.finishGame(
            game_id,
            direction,
            nonce
        ),
        private_key=private_key,
        tx_params=tx_params
    )
    
    return tx_hash


def force_finish_game(
    web3: Web3,
    contract: Contract,
    private_key: str,
    game_id: int,
    player1_direction: Direction,
    player1_nonce: int,
    player2_direction: Direction,
    player2_nonce: int
) -> str:
    """
    Force finish a game on the blockchain by calling the forceFinishGame function.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        private_key: The private key of the backend.
        game_id: The ID of the game.
        player1_direction: The direction of player1's position (Long or Short).
        player1_nonce: The nonce used when player1 posted the position.
        player2_direction: The direction of player2's position (Long or Short).
        player2_nonce: The nonce used when player2 posted the position.
        
    Returns:
        The transaction hash.
    """
    # Get account from private key
    account = web3.eth.account.from_key(private_key)
    backend_address = account.address
    
    # Prepare transaction parameters
    tx_params = {
        'from': backend_address
    }
    
    # Use the common transaction building, signing, and sending function
    tx_hash, receipt = build_sign_send_transaction(
        web3=web3,
        contract_function=contract.functions.forceFinishGame(
            game_id,
            player1_direction,
            player1_nonce,
            player2_direction,
            player2_nonce
        ),
        private_key=private_key,
        tx_params=tx_params
    )
    
    return tx_hash


def validate_join_game_transaction(
    web3: Web3,
    contract: Contract,
    game_id: int,
    tx_hash: str,
    pool_address: str
) -> Dict[str, Any]:
    """
    Validate a transaction that joined a game.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The expected game ID.
        tx_hash: The transaction hash.
        pool_address: The expected player2 pool address.
        
    Returns:
        A dictionary containing validation results.
    
    Raises:
        TransactionNotFound: If the transaction is not found.
        ValueError: If the transaction validation fails.
    """
    # Convert addresses to checksum format
    pool_address = Web3.to_checksum_address(pool_address)
    
    # Check if the transaction exists and is confirmed
    try:
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise ValueError("Transaction is not confirmed")
    except TransactionNotFound:
        raise ValueError("Transaction not found")
    
    # Check if the transaction was successful
    if tx_receipt["status"] != 1:
        raise ValueError("Transaction execution failed")
    
    # Get the transaction details
    tx = web3.eth.get_transaction(tx_hash)
    
    # Check if the transaction was sent to the contract address
    if tx["to"].lower() != contract.address.lower():
        raise ValueError(f"Transaction was not sent to the contract address {contract.address}")
    
    # Decode the transaction input data
    try:
        # Get the function signature for joinGame
        # Calculate the function signature (first 4 bytes of keccak hash of 'joinGame(uint256,address,uint256,bytes)')
        # Function signature should be exactly 4 bytes (8 hex characters)
        join_game_signature = web3.keccak(text='joinGame(uint256,address,uint256,bytes)').hex()[:8]
        
        # Check if the transaction called the joinGame function
        # Convert join_game_signature to bytes for comparison with tx["input"] which is in bytes format
        join_game_signature_bytes = bytes.fromhex(join_game_signature)
        
        if not tx["input"].startswith(join_game_signature_bytes):
            raise ValueError("Transaction did not call joinGame function")
        
        # Decode the function parameters
        decoded_input = contract.decode_function_input(tx["input"])
        
        # Check if the game ID matches
        if decoded_input[1]["gameId"] != game_id:
            raise ValueError(f"Transaction called joinGame with game ID {decoded_input[1]['gameId']} instead of {game_id}")
        
        # Check if the pool address matches
        if decoded_input[1]["pool"].lower() != pool_address.lower():
            raise ValueError(f"Transaction called joinGame with pool address {decoded_input[1]['pool']} instead of {pool_address}")
    except Exception as e:
        raise ValueError(f"Failed to decode transaction input: {e}")
    
    # Check if the game exists and has the expected player2 pool
    try:
        # Get the game info
        game_info = get_game_info(web3, contract, game_id)
        
        # Check if the game was joined with the expected pool address
        if game_info["player2Pool"].lower() != pool_address.lower():
            raise ValueError(f"Game {game_id} has player2 pool address {game_info['player2Pool']} instead of {pool_address}")
    except Exception as e:
        raise ValueError(f"Failed to verify game ID: {e}")
    
    # All validations passed
    return {
        "confirmed": True,
        "successful": True,
        "called_join_game": True,
        "game_id_match": True,
        "pool_address_match": True,
        "game_info": game_info
    }


def validate_post_position_transaction(
    web3: Web3,
    contract: Contract,
    game_id: int,
    tx_hash: str,
    direction: Direction,
    nonce: int
) -> Dict[str, Any]:
    """
    Validate a transaction that posted a position.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The expected game ID.
        tx_hash: The transaction hash.
        direction: The direction of the position (Long or Short).
        nonce: The nonce used for the position.
        
    Returns:
        A dictionary containing validation results.
    
    Raises:
        TransactionNotFound: If the transaction is not found.
        ValueError: If the transaction validation fails.
    """
    # Check if the transaction exists and is confirmed
    try:
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise ValueError("Transaction is not confirmed")
    except TransactionNotFound:
        raise ValueError("Transaction not found")
    
    # Check if the transaction was successful
    if tx_receipt["status"] != 1:
        raise ValueError("Transaction execution failed")
    
    # Get the transaction details
    tx = web3.eth.get_transaction(tx_hash)
    
    # Check if the transaction was sent to the contract address
    if tx["to"].lower() != contract.address.lower():
        raise ValueError(f"Transaction was not sent to the contract address {contract.address}")
    
    # Calculate the hashed direction
    encoded_data = encode(['uint256', 'uint8', 'uint256'], [game_id, direction, nonce])
    expected_hashed_direction = web3.keccak(encoded_data)
    
    # Decode the transaction input data
    try:
        # Get the function signature for postPosition
        # Calculate the function signature (first 4 bytes of keccak hash of 'postPosition(uint256,bytes32,bytes)')
        # Function signature should be exactly 4 bytes (8 hex characters)
        post_position_signature = web3.keccak(text='postPosition(uint256,bytes32,bytes)').hex()[:8]
        
        # Check if the transaction called the postPosition function
        # Convert post_position_signature to bytes for comparison with tx["input"] which is in bytes format
        post_position_signature_bytes = bytes.fromhex(post_position_signature)
        
        if not tx["input"].startswith(post_position_signature_bytes):
            raise ValueError("Transaction did not call postPosition function")
        
        # Decode the function parameters
        decoded_input = contract.decode_function_input(tx["input"])
        
        # Check if the game ID matches
        if decoded_input[1]["gameId"] != game_id:
            raise ValueError(f"Transaction called postPosition with game ID {decoded_input[1]['gameId']} instead of {game_id}")
        
        # Check if the hashed direction matches
        if decoded_input[1]["hashedDirection"] != expected_hashed_direction:
            raise ValueError(f"Transaction called postPosition with incorrect hashed direction")
    except Exception as e:
        raise ValueError(f"Failed to decode transaction input: {e}")
    
    # All validations passed
    return {
        "confirmed": True,
        "successful": True,
        "called_post_position": True,
        "game_id_match": True,
        "hashed_direction_match": True
    }


def validate_close_position_transaction(
    web3: Web3,
    contract: Contract,
    game_id: int,
    tx_hash: str,
    direction: Direction,
    nonce: int
) -> Dict[str, Any]:
    """
    Validate a transaction that closed a position.
    
    Args:
        web3: A Web3 instance.
        contract: The contract instance.
        game_id: The expected game ID.
        tx_hash: The transaction hash.
        direction: The direction of the position (Long or Short).
        nonce: The nonce used for the position.
        
    Returns:
        A dictionary containing validation results and position data.
    
    Raises:
        TransactionNotFound: If the transaction is not found.
        ValueError: If the transaction validation fails.
    """
    # Check if the transaction exists and is confirmed
    try:
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise ValueError("Transaction is not confirmed")
    except TransactionNotFound:
        raise ValueError("Transaction not found")
    
    # Check if the transaction was successful
    if tx_receipt["status"] != 1:
        raise ValueError("Transaction execution failed")
    
    # Get the transaction details
    tx = web3.eth.get_transaction(tx_hash)
    
    # Check if the transaction was sent to the contract address
    if tx["to"].lower() != contract.address.lower():
        raise ValueError(f"Transaction was not sent to the contract address {contract.address}")
    
    # Decode the transaction input data
    try:
        # Get the function signature for closePosition
        # Calculate the function signature (first 4 bytes of keccak hash of 'closePosition(uint256,uint8,uint256)')
        # Function signature should be exactly 4 bytes (8 hex characters)
        close_position_signature = web3.keccak(text='closePosition(uint256,uint8,uint256)').hex()[:8]
        
        # Check if the transaction called the closePosition function
        # Convert close_position_signature to bytes for comparison with tx["input"] which is in bytes format
        close_position_signature_bytes = bytes.fromhex(close_position_signature)
        
        if not tx["input"].startswith(close_position_signature_bytes):
            raise ValueError("Transaction did not call closePosition function")
        
        # Decode the function parameters
        decoded_input = contract.decode_function_input(tx["input"])
        
        # Check if the game ID matches
        if decoded_input[1]["gameId"] != game_id:
            raise ValueError(f"Transaction called closePosition with game ID {decoded_input[1]['gameId']} instead of {game_id}")
        
        # Check if the direction matches
        if decoded_input[1]["direction"] != direction:
            raise ValueError(f"Transaction called closePosition with direction {decoded_input[1]['direction']} instead of {direction}")
        
        # Check if the nonce matches
        if decoded_input[1]["nonce"] != nonce:
            raise ValueError(f"Transaction called closePosition with nonce {decoded_input[1]['nonce']} instead of {nonce}")
    except Exception as e:
        raise ValueError(f"Failed to decode transaction input: {e}")
    
    # Extract PositionClosed event from transaction logs
    position_data = None
    try:
        # Get the event signature for PositionClosed
        position_closed_event_signature = web3.keccak(text='PositionClosed(uint256,address,address,uint256,uint256,uint8,int256)').hex()
        
        # Find the PositionClosed event in the logs
        for log in tx_receipt.logs:
            # Check if the log is from the contract and has the PositionClosed event signature
            if log.address.lower() == contract.address.lower() and log.topics[0].hex() == position_closed_event_signature:
                # Decode the event data
                event_data = contract.events.PositionClosed().process_log(log)
                
                # Check if the event is for the correct game ID
                if event_data['args']['gameId'] == game_id:
                    position_data = {
                        "opening_price": event_data['args']['openingPrice'],
                        "closing_price": event_data['args']['closingPrice'],
                        "direction": event_data['args']['direction'],
                        "pnl": event_data['args']['pnl']
                    }
                    break
        
        if position_data is None:
            raise ValueError("PositionClosed event not found in transaction logs")
    except Exception as e:
        raise ValueError(f"Failed to extract PositionClosed event: {e}")
    
    # All validations passed
    return {
        "confirmed": True,
        "successful": True,
        "called_close_position": True,
        "game_id_match": True,
        "direction_match": True,
        "nonce_match": True,
        "position_data": position_data
    }