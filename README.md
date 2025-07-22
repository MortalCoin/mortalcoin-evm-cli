# MortalCoin EVM CLI

A command-line interface for interacting with MortalCoin EVM smart contracts.

## Features

- Create games on the MortalCoin smart contract
- Join existing games on the MortalCoin smart contract
- Post positions for games on the MortalCoin smart contract
- Validate game creation transactions
- Validate game joining transactions
- Track transaction status
- Retrieve game information

## Installation

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mortalcoin-evm-cli.git
   cd mortalcoin-evm-cli
   ```

2. Install the package:
   ```
   pip install -e .
   ```

### Using pip

```
pip install mortalcoin-evm-cli
```

## Usage

### Create a Game

Create a new game on the blockchain with a specified bet amount and pool address:

```
mortalcoin create-game-command \
  --private-key YOUR_PRIVATE_KEY \
  --rpc-url YOUR_RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --bet-amount BET_AMOUNT_IN_ETH \
  --pool-address POOL_ADDRESS
```

#### Parameters

- `--private-key`: Your Ethereum private key (required)
- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract (required)
- `--bet-amount`: Bet amount in ETH (required)
- `--pool-address`: Address of the pool (required)

### Join a Game

Join an existing game on the blockchain:

```
mortalcoin join-game-command \
  --rpc-url RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --game-id GAME_ID \
  --player1-privkey PLAYER1_PRIVATE_KEY \
  --player2-privkey PLAYER2_PRIVATE_KEY \
  --player2-pool PLAYER2_POOL_ADDRESS \
  --bet-amount BET_AMOUNT_IN_ETH
```

#### Parameters

- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract in 0x-prefixed hex format (required)
- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--player1-privkey`: Private key of player1 who created the game, in 0x-prefixed hex format (required)
- `--player2-privkey`: Private key of player2 who is joining the game, in 0x-prefixed hex format (required)
- `--player2-pool`: Address of player2's pool in 0x-prefixed hex format (required)
- `--bet-amount`: Bet amount in ETH (must match the game's bet amount) (required)

### Validate a Game Creation Transaction

Validate that a transaction successfully created a game with the expected parameters:

```
mortalcoin validate-create-game-command \
  --game-id GAME_ID \
  --tx-hash TRANSACTION_HASH \
  --pool-address POOL_ADDRESS \
  --contract-address CONTRACT_ADDRESS \
  --rpc-url RPC_URL
```

#### Parameters

- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--tx-hash`: Transaction hash in 0x-prefixed hex format (required)
- `--pool-address`: Pool address in 0x-prefixed hex format (required)
- `--contract-address`: Address of the MortalCoin smart contract (required)
- `--rpc-url`: URL of the Ethereum RPC endpoint (required)

### Validate a Game Join Transaction

Validate that a transaction successfully joined a game with the expected parameters:

```
mortalcoin validate-join-game-command \
  --rpc-url RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --game-id GAME_ID \
  --player2-pool PLAYER2_POOL_ADDRESS \
  --tx-hash TRANSACTION_HASH
```

#### Parameters

- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract in 0x-prefixed hex format (required)
- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--player2-pool`: Address of player2's pool in 0x-prefixed hex format (required)
- `--tx-hash`: Transaction hash in 0x-prefixed hex format (required)

### Post a Position

Post a position for a game on the blockchain:

```
mortalcoin post-position-command \
  --rpc-url RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --player-privkey PLAYER_PRIVATE_KEY \
  --backend-privkey BACKEND_PRIVATE_KEY \
  --game-id GAME_ID \
  --direction DIRECTION \
  --nonce NONCE
```

#### Parameters

- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract in 0x-prefixed hex format (required)
- `--player-privkey`: Private key of the player in 0x-prefixed hex format (required)
- `--backend-privkey`: Private key of the backend in 0x-prefixed hex format (required)
- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--direction`: Direction of the position (Long or Short) (required)
- `--nonce`: Nonce in 0x-prefixed hex format or decimal (required)

### Close a Position

Close a position for a game on the blockchain:

```
mortalcoin close-position-command \
  --rpc-url RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --game-id GAME_ID \
  --direction DIRECTION \
  --nonce NONCE \
  --player-privkey PLAYER_PRIVATE_KEY
```

#### Parameters

- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract in 0x-prefixed hex format (required)
- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--direction`: Direction of the position (Long or Short) (required)
- `--nonce`: Nonce in 0x-prefixed hex format or decimal (required)
- `--player-privkey`: Private key of the player in 0x-prefixed hex format (required)

### Finish a Game

Finish a game on the blockchain by calling the finishGame function:

```
mortalcoin finish-game-command \
  --rpc-url RPC_URL \
  --contract-address CONTRACT_ADDRESS \
  --player-privkey PLAYER_PRIVATE_KEY \
  --game-id GAME_ID \
  --direction DIRECTION \
  --nonce NONCE
```

#### Parameters

- `--rpc-url`: URL of the Ethereum RPC endpoint (required)
- `--contract-address`: Address of the MortalCoin smart contract in 0x-prefixed hex format (required)
- `--player-privkey`: Private key of the player in 0x-prefixed hex format (required)
- `--game-id`: Game ID in 0x-prefixed hex format or decimal (required)
- `--direction`: Direction of the position (Long or Short) (optional, defaults to Long)
- `--nonce`: Nonce in 0x-prefixed hex format or decimal (optional, defaults to 0)

### Environment Variables

You can also set the parameters using environment variables:

- `MORTALCOIN_PRIVATE_KEY`: Your Ethereum private key
- `MORTALCOIN_RPC_URL`: URL of the Ethereum RPC endpoint
- `MORTALCOIN_CONTRACT_ADDRESS`: Address of the MortalCoin smart contract
- `MORTALCOIN_BET_AMOUNT`: Bet amount in ETH
- `MORTALCOIN_POOL_ADDRESS`: Address of the pool

You can create a `.env` file in the current directory with these variables:

```
MORTALCOIN_PRIVATE_KEY=your_private_key
MORTALCOIN_RPC_URL=your_rpc_url
MORTALCOIN_CONTRACT_ADDRESS=contract_address
MORTALCOIN_BET_AMOUNT=bet_amount
MORTALCOIN_POOL_ADDRESS=pool_address
```

## Security Considerations

- **Never share your private key**: The private key gives full control over your Ethereum account. Never share it with anyone.
- **Use environment variables or .env files**: Avoid passing your private key as a command-line argument, as it may be visible in your command history.
- **Consider using a dedicated account**: Use a dedicated account with limited funds for interacting with the smart contract.

## Development

### Requirements

- Python 3.8 or higher
- web3.py 7.12.1
- click 8.0.0 or higher
- python-dotenv 0.19.0 or higher

### Setup Development Environment

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mortalcoin-evm-cli.git
   cd mortalcoin-evm-cli
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```
   pip install -e .
   ```

## License

See the [LICENSE](LICENSE) file for details.