# MortalCoin EVM CLI

A command-line interface for interacting with MortalCoin EVM smart contracts.

## Features

- Create games on the MortalCoin smart contract
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

## Example

```
mortalcoin create-game-command \
  --private-key 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --rpc-url https://mainnet.infura.io/v3/your-project-id \
  --contract-address 0x1234567890123456789012345678901234567890 \
  --bet-amount 0.1 \
  --pool-address 0x0987654321098765432109876543210987654321
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