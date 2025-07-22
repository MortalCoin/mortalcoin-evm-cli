"""
Command-line interface for MortalCoin EVM CLI.

This module provides the command-line interface for interacting with the MortalCoin
smart contract on the Ethereum blockchain.
"""

import json
import sys

import click
from dotenv import load_dotenv
from web3 import Web3

from mortalcoin_evm_cli.blockchain import (
    Direction,
    get_web3_connection,
    get_contract,
    create_game,
    get_game_info,
    validate_create_game_transaction,
    validate_join_game_transaction,
    join_game,
    post_position,
)


# Load environment variables from .env file if it exists
load_dotenv()


@click.group()
@click.version_option()
def main():
    """MortalCoin EVM CLI tool for interacting with the MortalCoin smart contract."""
    pass


@main.command()
@click.option(
    "--private-key",
    required=True,
    help="Private key of the user's Ethereum account.",
    envvar="MORTALCOIN_PRIVATE_KEY",
)
@click.option(
    "--rpc-url",
    required=True,
    help="URL of the Ethereum RPC endpoint.",
    envvar="MORTALCOIN_RPC_URL",
)
@click.option(
    "--contract-address",
    required=True,
    help="Address of the MortalCoin smart contract.",
    envvar="MORTALCOIN_CONTRACT_ADDRESS",
)
@click.option(
    "--bet-amount",
    required=True,
    type=float,
    help="Bet amount in ETH.",
    envvar="MORTALCOIN_BET_AMOUNT",
)
@click.option(
    "--pool-address",
    required=True,
    help="Address of the pool.",
    envvar="MORTALCOIN_POOL_ADDRESS",
)
def create_game_command(
    private_key: str,
    rpc_url: str,
    contract_address: str,
    bet_amount: float,
    pool_address: str,
):
    """
    Create a new game on the blockchain.
    
    This command creates a new game on the blockchain with the specified bet amount
    and pool address. It then waits for the transaction to be mined and retrieves
    the game information.
    """
    try:
        # Connect to the blockchain
        web3 = get_web3_connection(rpc_url)
        
        # Validate addresses
        if not Web3.is_address(contract_address):
            click.echo(f"Error: Invalid contract address: {contract_address}")
            sys.exit(1)
        
        if not Web3.is_address(pool_address):
            click.echo(f"Error: Invalid pool address: {pool_address}")
            sys.exit(1)
        
        # Convert addresses to checksum format
        contract_address = Web3.to_checksum_address(contract_address)
        pool_address = Web3.to_checksum_address(pool_address)
        
        # Convert bet amount from ETH to Wei
        bet_amount_wei = Web3.to_wei(bet_amount, "ether")
        
        # Get the contract instance
        contract = get_contract(web3, contract_address)
        
        # Create the game
        click.echo(f"Creating game with bet amount {bet_amount} ETH and pool address {pool_address}...")
        tx_hash, game_id = create_game(
            web3=web3,
            contract=contract,
            private_key=private_key,
            bet_amount=bet_amount_wei,
            pool_address=pool_address,
        )
        
        click.echo(f"Transaction hash: {tx_hash}")
        
        if game_id is not None:
            click.echo(f"Game created with ID: {game_id}")
            
            # Get the game information
            click.echo("Retrieving game information...")
            game_info = get_game_info(web3, contract, game_id)
            
            # Print the game information
            click.echo("Game information:")
            click.echo(json.dumps(game_info, indent=2))
        else:
            click.echo("Failed to retrieve game ID.")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--game-id",
    required=True,
    help="Game ID in 0x-prefixed hex format.",
)
@click.option(
    "--tx-hash",
    required=True,
    help="Transaction hash in 0x-prefixed hex format.",
)
@click.option(
    "--pool-address",
    required=True,
    help="Pool address in 0x-prefixed hex format.",
)
@click.option(
    "--contract-address",
    required=True,
    help="Smart contract address in 0x-prefixed hex format.",
    envvar="MORTALCOIN_CONTRACT_ADDRESS",
)
@click.option(
    "--rpc-url",
    required=True,
    help="URL of the Ethereum RPC endpoint.",
    envvar="MORTALCOIN_RPC_URL",
)
def validate_create_game_command(
    game_id: str,
    tx_hash: str,
    pool_address: str,
    contract_address: str,
    rpc_url: str,
):
    """
    Validate a transaction that created a game.
    
    This command validates that:
    - The transaction is confirmed
    - The transaction execution was successful
    - The transaction actually called createGame with the expected pool address
    - The transaction call returned the expected gameId
    """
    try:
        # Connect to the blockchain
        web3 = get_web3_connection(rpc_url)
        
        # Validate addresses
        if not Web3.is_address(contract_address):
            click.echo(f"Error: Invalid contract address: {contract_address}")
            sys.exit(1)
        
        if not Web3.is_address(pool_address):
            click.echo(f"Error: Invalid pool address: {pool_address}")
            sys.exit(1)
        
        # Convert addresses to checksum format
        contract_address = Web3.to_checksum_address(contract_address)
        pool_address = Web3.to_checksum_address(pool_address)
        
        # Convert game_id from hex to int if it's in hex format
        if game_id.startswith("0x"):
            game_id_int = int(game_id, 16)
        else:
            try:
                game_id_int = int(game_id)
            except ValueError:
                click.echo(f"Error: Invalid game ID format: {game_id}. Must be a decimal number or 0x-prefixed hex.")
                sys.exit(1)
        
        # Get the contract instance
        contract = get_contract(web3, contract_address)
        
        # Validate the transaction
        click.echo(f"Validating transaction {tx_hash} for game ID {game_id}...")
        validation_result = validate_create_game_transaction(
            web3=web3,
            contract=contract,
            game_id=game_id_int,
            tx_hash=tx_hash,
            pool_address=pool_address,
        )
        
        # Print the validation results
        click.echo("Validation successful!")
        click.echo("Results:")
        click.echo(f"- Transaction confirmed: {validation_result['confirmed']}")
        click.echo(f"- Transaction successful: {validation_result['successful']}")
        click.echo(f"- Called createGame function: {validation_result['called_create_game']}")
        click.echo(f"- Pool address matches: {validation_result['pool_address_match']}")
        click.echo(f"- Game ID valid: {validation_result['game_id_valid']}")
        
        # Print the game information
        click.echo("\nGame information:")
        click.echo(json.dumps(validation_result['game_info'], indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--rpc-url",
    required=True,
    help="URL of the Ethereum RPC endpoint.",
    envvar="MORTALCOIN_RPC_URL",
)
@click.option(
    "--contract-address",
    required=True,
    help="Address of the MortalCoin smart contract in 0x-prefixed hex format.",
    envvar="MORTALCOIN_CONTRACT_ADDRESS",
)
@click.option(
    "--game-id",
    required=True,
    help="Game ID in 0x-prefixed hex format or decimal.",
)
@click.option(
    "--player2-pool",
    required=True,
    help="Address of player2's pool in 0x-prefixed hex format.",
)
@click.option(
    "--tx-hash",
    required=True,
    help="Transaction hash in 0x-prefixed hex format.",
)
def validate_join_game_command(
    rpc_url: str,
    contract_address: str,
    game_id: str,
    player2_pool: str,
    tx_hash: str,
):
    """
    Validate a transaction that joined a game.
    
    This command validates that:
    - The transaction is confirmed
    - The transaction execution was successful
    - The transaction actually called joinGame with the expected game ID and pool address
    """
    try:
        # Connect to the blockchain
        web3 = get_web3_connection(rpc_url)
        
        # Validate addresses
        if not Web3.is_address(contract_address):
            click.echo(f"Error: Invalid contract address: {contract_address}")
            sys.exit(1)
        
        if not Web3.is_address(player2_pool):
            click.echo(f"Error: Invalid pool address: {player2_pool}")
            sys.exit(1)
        
        # Convert addresses to checksum format
        contract_address = Web3.to_checksum_address(contract_address)
        player2_pool = Web3.to_checksum_address(player2_pool)
        
        # Convert game_id from hex to int if it's in hex format
        if game_id.startswith("0x"):
            game_id_int = int(game_id, 16)
        else:
            try:
                game_id_int = int(game_id)
            except ValueError:
                click.echo(f"Error: Invalid game ID format: {game_id}. Must be a decimal number or 0x-prefixed hex.")
                sys.exit(1)
        
        # Get the contract instance
        contract = get_contract(web3, contract_address)
        
        # Validate the transaction
        click.echo(f"Validating transaction {tx_hash} for game ID {game_id}...")
        validation_result = validate_join_game_transaction(
            web3=web3,
            contract=contract,
            game_id=game_id_int,
            tx_hash=tx_hash,
            pool_address=player2_pool,
        )
        
        # Print the validation results
        click.echo("Validation successful!")
        click.echo("Results:")
        click.echo(f"- Transaction confirmed: {validation_result['confirmed']}")
        click.echo(f"- Transaction successful: {validation_result['successful']}")
        click.echo(f"- Called joinGame function: {validation_result['called_join_game']}")
        click.echo(f"- Game ID matches: {validation_result['game_id_match']}")
        click.echo(f"- Pool address matches: {validation_result['pool_address_match']}")
        
        # Print the game information
        click.echo("\nGame information:")
        click.echo(json.dumps(validation_result['game_info'], indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--rpc-url",
    required=True,
    help="URL of the Ethereum RPC endpoint.",
    envvar="MORTALCOIN_RPC_URL",
)
@click.option(
    "--contract-address",
    required=True,
    help="Address of the MortalCoin smart contract in 0x-prefixed hex format.",
    envvar="MORTALCOIN_CONTRACT_ADDRESS",
)
@click.option(
    "--game-id",
    required=True,
    help="Game ID in 0x-prefixed hex format.",
)
@click.option(
    "--player1-privkey",
    required=True,
    help="Private key of player1 in 0x-prefixed hex format.",
)
@click.option(
    "--player2-privkey",
    required=True,
    help="Private key of player2 in 0x-prefixed hex format.",
)
@click.option(
    "--player2-pool",
    required=True,
    help="Address of player2's pool in 0x-prefixed hex format.",
)
@click.option(
    "--bet-amount",
    required=True,
    type=float,
    help="Bet amount in ETH (must match the game's bet amount).",
)
def join_game_command(
    rpc_url: str,
    contract_address: str,
    game_id: str,
    player1_privkey: str,
    player2_privkey: str,
    player2_pool: str,
    bet_amount: float,
):
    """
    Join an existing game on the blockchain.
    
    This command allows player2 to join a game created by player1. It requires:
    - A signature from player1 authorizing player2 to join
    - The same bet amount as specified when the game was created
    - A whitelisted pool address for player2
    
    The command signs the request using player1's private key, then submits a transaction
    from player2's account to join the game. It waits for confirmation and prints the
    updated state of the game.
    """
    try:
        # Connect to the blockchain
        web3 = get_web3_connection(rpc_url)
        
        # Validate addresses
        if not Web3.is_address(contract_address):
            click.echo(f"Error: Invalid contract address: {contract_address}")
            sys.exit(1)
        
        if not Web3.is_address(player2_pool):
            click.echo(f"Error: Invalid player2 pool address: {player2_pool}")
            sys.exit(1)
        
        # Convert addresses to checksum format
        contract_address = Web3.to_checksum_address(contract_address)
        player2_pool = Web3.to_checksum_address(player2_pool)
        
        # Convert game_id from hex to int if it's in hex format
        if game_id.startswith("0x"):
            game_id_int = int(game_id, 16)
        else:
            try:
                game_id_int = int(game_id)
            except ValueError:
                click.echo(f"Error: Invalid game ID format: {game_id}. Must be a decimal number or 0x-prefixed hex.")
                sys.exit(1)
        
        # Convert bet amount from ETH to Wei
        bet_amount_wei = Web3.to_wei(bet_amount, "ether")
        
        # Get the contract instance
        contract = get_contract(web3, contract_address)
        
        # Join the game
        click.echo(f"Joining game {game_id} with bet amount {bet_amount} ETH and player2 pool address {player2_pool}...")
        tx_hash, game_info = join_game(
            web3=web3,
            contract=contract,
            game_id=game_id_int,
            player1_private_key=player1_privkey,
            player2_private_key=player2_privkey,
            player2_pool=player2_pool,
            bet_amount=bet_amount_wei,
        )
        
        click.echo(f"Transaction hash: {tx_hash}")
        
        # Print the game information
        click.echo("Game information:")
        click.echo(json.dumps(game_info, indent=2))
    
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.option(
    "--rpc-url",
    required=True,
    help="URL of the Ethereum RPC endpoint.",
    envvar="MORTALCOIN_RPC_URL",
)
@click.option(
    "--contract-address",
    required=True,
    help="Address of the MortalCoin smart contract in 0x-prefixed hex format.",
    envvar="MORTALCOIN_CONTRACT_ADDRESS",
)
@click.option(
    "--player-privkey",
    required=True,
    help="Private key of the player in 0x-prefixed hex format.",
)
@click.option(
    "--backend-privkey",
    required=True,
    help="Private key of the backend in 0x-prefixed hex format.",
)
@click.option(
    "--game-id",
    required=True,
    help="Game ID in 0x-prefixed hex format.",
)
@click.option(
    "--direction",
    required=True,
    type=click.Choice(["Long", "Short"], case_sensitive=False),
    help="Direction of the position (Long or Short).",
)
@click.option(
    "--nonce",
    required=True,
    help="Nonce in 0x-prefixed hex format.",
)
def post_position_command(
    rpc_url: str,
    contract_address: str,
    player_privkey: str,
    backend_privkey: str,
    game_id: str,
    direction: str,
    nonce: str,
):
    """
    Post a position on the blockchain.
    
    This command allows a player to post a position for a game. It requires:
    - The player's private key
    - The backend's private key to sign the position
    - The game ID
    - The direction of the position (Long or Short)
    - A nonce for the position
    
    The command calculates the hashed direction, gets a signature from the backend,
    and submits a transaction from the player's account to post the position.
    It waits for confirmation and prints the transaction hash.
    """
    try:
        # Connect to the blockchain
        web3 = get_web3_connection(rpc_url)
        
        # Validate addresses
        if not Web3.is_address(contract_address):
            click.echo(f"Error: Invalid contract address: {contract_address}")
            sys.exit(1)
        
        # Convert addresses to checksum format
        contract_address = Web3.to_checksum_address(contract_address)
        
        # Convert game_id from hex to int if it's in hex format
        if game_id.startswith("0x"):
            game_id_int = int(game_id, 16)
        else:
            try:
                game_id_int = int(game_id)
            except ValueError:
                click.echo(f"Error: Invalid game ID format: {game_id}. Must be a decimal number or 0x-prefixed hex.")
                sys.exit(1)
        
        # Convert direction to enum value
        direction_enum = Direction.Long if direction.lower() == "long" else Direction.Short
        
        # Convert nonce from hex to int if it's in hex format
        if nonce.startswith("0x"):
            nonce_int = int(nonce, 16)
        else:
            try:
                nonce_int = int(nonce)
            except ValueError:
                click.echo(f"Error: Invalid nonce format: {nonce}. Must be a decimal number or 0x-prefixed hex.")
                sys.exit(1)
        
        # Get the contract instance
        contract = get_contract(web3, contract_address)
        
        # Post the position
        click.echo(f"Posting {direction} position for game {game_id} with nonce {nonce}...")
        tx_hash = post_position(
            web3=web3,
            contract=contract,
            player_private_key=player_privkey,
            backend_private_key=backend_privkey,
            game_id=game_id_int,
            direction=direction_enum,
            nonce=nonce_int,
        )
        
        click.echo(f"Transaction hash: {tx_hash}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()