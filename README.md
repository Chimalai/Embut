# Intuition Testnet Bridge Bot

A powerful and automated Python bot for bridging assets between the Intuition Testnet and Base Sepolia Testnet. This tool is designed to simplify repetitive bridging tasks, making it ideal for network testing, transaction farming, or interacting with testnet protocols.

The bot supports multiple accounts, features automatic proxy detection, and provides a clean, minimalist user interface.

## Features

  - **Automated Bridging**: Automatically bridges assets between Intuition and Base Sepolia.
  - **Randomized Transactions**: Randomly chooses the bridge direction (Intuition to Base, or Base to Intuition) for each transaction to simulate more human-like behavior.
  - **Multi-Account Support**: Securely manages and cycles through multiple private keys from a `.env` file.
  - **Automatic Proxy Detection**: If a `proxies.txt` file with valid proxies is found, the bot will automatically use them. If not, it runs without proxies. No manual configuration is needed.
  - **User-Friendly Interface**: Asks for the number of transactions and the amount at runtime.
  - **Dynamic Countdown**: Features a self-erasing countdown timer between transactions to keep the terminal output clean.
  - **24-Hour Cycle**: After processing all accounts, the bot will wait for 24 hours before starting the next cycle automatically.

## Project Structure

The repository contains the following files:

  - **`bot.py`**: The main executable script for the bot. This is the entry point of the application.
  - **`config.py`**: The core configuration layer for the PetrukStar framework. **This file is for internal use only and should not be modified.** It handles core access and licensing details.
  - **`.env`**: User-defined environment variables. This is where you must store your private keys.
  - **`proxies.txt`**: (Optional) A list of proxies, one per line. The bot will automatically detect and use this file if it exists and is not empty.
  - **`requirements.txt`**: A list of all Python dependencies required to run the bot.
  - **`README.md`**: This file, providing documentation and instructions.

## Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

  - Python 3.8 or higher
  - pip (Python package installer)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Chimalai/Embut.git
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd Embut
    ```

3.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Install the required packages:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The bot requires a `.env` file for private keys and optionally accepts a `proxies.txt` file.

### 1\. Private Keys (`.env` file)

This is the primary method for securely storing your account private keys.

1.  Create a file named `.env` in the root of the project directory.
2.  Add your private keys, one per line, with the prefix `PRIVATE_KEY_`.

**Example `.env` file:**

```env
PRIVATE_KEY_1=0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
PRIVATE_KEY_2=0x4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b1c2d
```

### 2\. Proxies (`proxies.txt` file) - Optional

The bot will automatically detect and use proxies if this file exists and is not empty.

1.  Create a file named `proxies.txt` in the root of the project directory.
2.  Add your proxies, one per line. The bot supports `http`, `https`, `socks4`, and `socks5` formats.

**Example `proxies.txt` file:**

```txt
http://user:pass@host:port
socks5://user:pass@host:port
```

If this file is empty or does not exist, the bot will run all transactions without a proxy.

## Usage

Once the configuration is complete, you can run the bot with a single command:

```bash
python bot.py
```

The script will then prompt you to enter the following:

1.  **Bridge Transaction Count**: The number of bridge transactions to perform for *each* account.
2.  **Enter Bridge Amount daily**: The amount of tTRUST to bridge in each transaction.

After you provide the inputs, the bot will display the balances of all accounts and begin the bridging process.

## ⚠️ Disclaimer

  - This script is provided for educational purposes only.
  - **Never share your `.env` file or your private keys with anyone.**
  - The author is not responsible for any loss of funds. Use this bot at your own risk.

## License

Distributed under the MIT License. See `LICENSE` for more information.
