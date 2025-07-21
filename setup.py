from setuptools import setup, find_packages

setup(
    name="mortalcoin-evm-cli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "web3==7.12.1",
        "click>=8.0.0",
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "mortalcoin=mortalcoin_evm_cli.cli:main",
        ],
    },
    python_requires=">=3.8",
    description="CLI tool for interacting with MortalCoin EVM smart contracts",
    author="MortalCoin Team",
)