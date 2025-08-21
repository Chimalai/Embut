from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from datetime import datetime
from colorama import *
import asyncio, random, json, re, os, pytz
from dotenv import load_dotenv

wib = pytz.timezone('Asia/Jakarta')

class Intuition:
    def __init__(self) -> None:
        self.INTUITION_RPC_URL = "https://testnet.rpc.intuition.systems/http"
        self.INTUITION_EXPLORER = "https://testnet.explorer.intuition.systems/tx/"
        self.BASE_SEPOLIA_RPC_URL = "https://base-sepolia.rpc.dev.caldera.xyz/"
        self.BASE_SEPOLIA_EXPLORER = "https://sepolia.basescan.org/tx/"
        self.TTRUST_CONTRACT_ADDRESS = "0xA54b4E6e356b963Ee00d1C947f478d9194a1a210"
        self.ROLLUP_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000000"
        self.ARB_SYS_ADDRESS = "0x0000000000000000000000000000000000000064"
        self.INBOX_ADDRESS = "0xBd983e1350263d1BE5DE4AEB8b1704A0Ea0be350"
        self.OUTBOX_ADDRESS = "0xBEC1462f12f8a968e07ae3D60C8C32Cd32A23826"
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]},
            {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]}
        ]''')
        self.CONTRACT_ABI = [
            {
                "type": "function",
                "name": "withdrawEth",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "address","name": "destination","type": "address" }
                ],
                "outputs": [
                    { "internalType": "uint256","name": "","type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "createRetryableTicket",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "to", "type": "address" },
                    { "internalType": "uint256", "name": "l2CallValue", "type": "uint256" },
                    { "internalType": "uint256", "name": "maxSubmissionCost", "type": "uint256" },
                    { "internalType": "address", "name": "excessFeeRefundAddress", "type": "address" },
                    { "internalType": "address", "name": "callValueRefundAddress", "type": "address" },
                    { "internalType": "uint256", "name": "gasLimit", "type": "uint256" },
                    { "internalType": "uint256", "name": "maxFeePerGas", "type": "uint256" },
                    { "internalType": "uint256", "name": "tokenTotalFeeAmount", "type": "uint256" },
                    { "internalType": "bytes", "name": "data", "type": "bytes" }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "", "type": "uint256" }
                ]
            },
            {
                "type": "function",
                "name": "executeTransaction",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "bytes32[]", "name": "proof", "type": "bytes32[]" },
                    { "internalType": "uint256", "name": "index", "type": "uint256" },
                    { "internalType": "address", "name": "l2Sender", "type": "address" },
                    { "internalType": "address", "name": "to", "type": "address" },
                    { "internalType": "uint256", "name": "l2Block", "type": "uint256" },
                    { "internalType": "uint256", "name": "l1Block", "type": "uint256" },
                    { "internalType": "uint256", "name": "l2Timestamp", "type": "uint256" },
                    { "internalType": "uint256", "name": "value", "type": "uint256" },
                    { "internalType": "bytes", "name": "data", "type": "bytes" }
                ],
                "outputs": []
            }
        ]
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.bridge_count = 0
        self.bridge_amount = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(message, flush=True)

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self):
        filename = "proxies.txt"
        try:
            if not os.path.exists(filename):
                return False
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                return False

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies detected. Total: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
            return True
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            return False

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    async def get_web3_with_check(self, address: str, rpc_url: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
        
    async def get_token_balance(self, address: str, rpc_url: str, contract_address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, rpc_url, use_proxy)

            if contract_address == self.ROLLUP_CONTRACT_ADDRESS:
                balance = web3.eth.get_balance(address)
                decimals = 18
            else:
                token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
                balance = token_contract.functions.balanceOf(address).call()
                decimals = token_contract.functions.decimals().call()

            token_balance = balance / (10 ** decimals)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
    
    async def approving_token(self, account: str, address: str, spender_address: str, amount_to_wei: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, self.BASE_SEPOLIA_RPC_URL, use_proxy)
            
            spender = web3.to_checksum_address(spender_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.TTRUST_CONTRACT_ADDRESS), abi=self.ERC20_CONTRACT_ABI)

            allowance = token_contract.functions.allowance(address, spender).call()
            if allowance < amount_to_wei:
                approve_data = token_contract.functions.approve(spender, amount_to_wei)

                estimated_gas = approve_data.estimate_gas({"from": address})
                max_priority_fee = web3.to_wei(0.001, "gwei")
                max_fee = max_priority_fee

                approve_tx = approve_data.build_transaction({
                    "from": address,
                    "gas": int(estimated_gas * 1.2),
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": web3.eth.get_transaction_count(address, "pending"),
                    "chainId": web3.eth.chain_id,
                })

                tx_hash = await self.send_raw_transaction_with_retries(account, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

                block_number = receipt.blockNumber
                
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Approve :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Block   :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Tx Hash :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {tx_hash} {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}     Explorer:{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {self.BASE_SEPOLIA_EXPLORER}{tx_hash} {Style.RESET_ALL}"
                )
                await self.print_timer()
            
            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")
        
    async def perform_withdraw_eth(self, account: str, address: str, amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, self.INTUITION_RPC_URL, use_proxy)

            amount_to_wei = web3.to_wei(amount, "ether")

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.ARB_SYS_ADDRESS), abi=self.CONTRACT_ABI)

            withdraw_data = token_contract.functions.withdrawEth(address)

            estimated_gas = withdraw_data.estimate_gas({"from":address, "value":amount_to_wei})
            max_priority_fee = web3.to_wei(0.1, "gwei")
            max_fee = max_priority_fee

            withdraw_tx = withdraw_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, withdraw_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber

            return tx_hash, block_number

        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
        
    async def perform_create_retryable_ticket(self, account: str, address: str, amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, self.BASE_SEPOLIA_RPC_URL, use_proxy)

            amount_to_wei = web3.to_wei(amount, "ether")

            amount_with_fees = (27514 * 600000000) + 0 + amount_to_wei

            await self.approving_token(account, address, self.INBOX_ADDRESS, amount_with_fees, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.INBOX_ADDRESS), abi=self.CONTRACT_ABI)

            retryable_ticket_data = token_contract.functions.createRetryableTicket(
                address, amount_to_wei, 0, address, address, 27514, 600000000, amount_with_fees, b''
            )

            estimated_gas = retryable_ticket_data.estimate_gas({"from":address})
            max_priority_fee = web3.to_wei(0.001, "gwei")
            max_fee = max_priority_fee

            retryable_ticket_tx = retryable_ticket_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, retryable_ticket_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber

            return tx_hash, block_number

        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}     Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
    
    async def print_timer(self):
        delay = random.randint(self.min_delay, self.max_delay)
        if delay <= 0:
            self.log("")
            return

        for remaining in range(delay, 0, -1):
            print(
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}  ",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

        print(" " * 70, end="\r", flush=True)
        self.log("")

    def print_question(self):
        while True:
            try:
                bridge_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Bridge Transaction Count: {Style.RESET_ALL}").strip())
                if bridge_count > 0:
                    self.bridge_count = bridge_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter a positive number.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter a number.{Style.RESET_ALL}")

        while True:
            try:
                bridge_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Bridge Amount daily: {Style.RESET_ALL}").strip())
                if bridge_amount > 0:
                    self.bridge_amount = bridge_amount
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Amount must be greater than 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Please enter a number.{Style.RESET_ALL}")
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    await asyncio.sleep(1)
                    continue

                return False

            return True
        
    async def process_perform_withdraw_eth(self, account: str, address: str, amount: float, use_proxy: bool):
        tx_hash, _ = await self.perform_withdraw_eth(account, address, amount, use_proxy)
        if tx_hash:
            self.log(
                f"{Fore.GREEN+Style.BRIGHT}Success :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.INTUITION_EXPLORER}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.RED+Style.BRIGHT}Failed to perform bridge from Intuition.{Style.RESET_ALL}"
            )
        
    async def process_perform_create_retryable_ticket(self, account: str, address: str, amount: float, use_proxy: bool):
        tx_hash, _ = await self.perform_create_retryable_ticket(account, address, amount, use_proxy)
        if tx_hash:
            self.log(
                f"{Fore.GREEN+Style.BRIGHT}Success :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.BASE_SEPOLIA_EXPLORER}{tx_hash} {Style.RESET_ALL}"
            )
        else:
            self.log(
                f"{Fore.RED+Style.BRIGHT}Failed to perform bridge from Base Sepolia.{Style.RESET_ALL}"
            )

    async def process_option_1(self, account: str, address: str, use_proxy: bool):
        balance = await self.get_token_balance(address, self.INTUITION_RPC_URL, self.ROLLUP_CONTRACT_ADDRESS, use_proxy)
        if not balance or balance <= self.bridge_amount:
            self.log(
                f"{Fore.YELLOW+Style.BRIGHT}Failed  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} Insufficient balance on Intuition.{Style.RESET_ALL}"
            )
            return

        await self.process_perform_withdraw_eth(account, address, self.bridge_amount, use_proxy)

    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        balance = await self.get_token_balance(address, self.BASE_SEPOLIA_RPC_URL, self.TTRUST_CONTRACT_ADDRESS, use_proxy)
        if not balance or balance <= self.bridge_amount:
            self.log(
                f"{Fore.YELLOW+Style.BRIGHT}Failed  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} Insufficient balance on Base Sepolia.{Style.RESET_ALL}"
            )
            return

        await self.process_perform_create_retryable_ticket(account, address, self.bridge_amount, use_proxy)
        
    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        if use_proxy:
            is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
            if not is_valid:
                return

        if option == 1:
            for i in range(self.bridge_count):
                await self.process_option_1(account, address, use_proxy)
                await self.print_timer()

        elif option == 2:
            for i in range(self.bridge_count):
                await self.process_option_2(account, address, use_proxy)
                await self.print_timer()

        elif option == 3:
            for i in range(self.bridge_count):
                bridge = random.choice([self.process_option_1, self.process_option_2])
                await bridge(account, address, use_proxy)
                await self.print_timer()

    async def main(self):
        try:
            load_dotenv()
            accounts = [value for key, value in os.environ.items() if key.startswith("PRIVATE_KEY_")]

            if not accounts:
                self.log(f"{Fore.RED + Style.BRIGHT}No private keys found in .env file.{Style.RESET_ALL}")
                self.log(f"{Fore.YELLOW + Style.BRIGHT}Ensure the format is 'PRIVATE_KEY_1=0x...'{Style.RESET_ALL}")
                return
            
            option = 3
            self.min_delay = 2
            self.max_delay = 3
            
            self.print_question()

            while True:
                use_proxy = await self.load_proxies()
                
                self.clear_terminal()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Accounts : {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )
                
                for acc_check in accounts:
                    address_check = self.generate_address(acc_check)
                    if not address_check:
                        self.log(f"{Fore.RED+Style.BRIGHT}Invalid Private Key detected, skipping balance check.{Style.RESET_ALL}")
                        continue
                    
                    self.log(f"{Fore.WHITE+Style.BRIGHT}Address: {self.mask_account(address_check)}{Style.RESET_ALL}")

                    base_balance = await self.get_token_balance(address_check, self.BASE_SEPOLIA_RPC_URL, self.TTRUST_CONTRACT_ADDRESS, use_proxy)
                    base_balance_str = f"{base_balance:.4f}" if base_balance is not None else "Error"
                    self.log(f"  {Fore.CYAN}Base Sepolia Balance: {base_balance_str} tTRUST{Style.RESET_ALL}")

                    intuition_balance = await self.get_token_balance(address_check, self.INTUITION_RPC_URL, self.ROLLUP_CONTRACT_ADDRESS, use_proxy)
                    intuition_balance_str = f"{intuition_balance:.4f}" if intuition_balance is not None else "Error"
                    self.log(f"  {Fore.CYAN}Intuition Balance   : {intuition_balance_str} tTRUST{Style.RESET_ALL}")

                self.log("\nStarting bridge process in 5 seconds...")
                await asyncio.sleep(5)
                
                for i, account in enumerate(accounts):
                    if account:
                        address = self.generate_address(account)
                        self.log(f"\n{Fore.WHITE + Style.BRIGHT}{self.mask_account(address)}{Style.RESET_ALL}")

                        if not address:
                            self.log(
                                f"{Fore.RED+Style.BRIGHT} Invalid Private Key or Libraries Version Not Supported {Style.RESET_ALL}"
                            )
                            continue
                        
                        await self.process_accounts(account, address, option, use_proxy, False)
                        await asyncio.sleep(3)

                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Waiting for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except ( Exception, ValueError ) as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Intuition()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"\n{Fore.RED + Style.BRIGHT}[ EXITING ]{Style.RESET_ALL}"
        )