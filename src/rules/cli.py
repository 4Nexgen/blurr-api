from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from eth_account import Account

from web3 import Web3

import json
import subprocess
import re
import sys

from src.helpers.stream_file import StreamFileHelper

import os
from dotenv import load_dotenv
load_dotenv()

class CLIRule:
    def __init__(self):

        self.ssh_user = "pc"
        self.ssh_host = "1.212.199.98"
        self.ssh_port = "2105"
        self.ssh_password = "Xode@2024"
        self.remote_home = f"/home/{self.ssh_user}"
    
        self.CLI_DIR_PATH = Path(os.getenv("CLI_DIR")) 

        self.RPC_URL = os.getenv("RPC_URL")
        self.PRIVATE_KEY = os.getenv("PRIVATE_KEY")

        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.account = Account.from_key(self.PRIVATE_KEY)
    
    def directory_list(self) -> StreamingResponse:
        try:
            contracts_dir = self.CLI_DIR_PATH / "contracts"

            if not contracts_dir.exists() or not contracts_dir.is_dir():
                raise HTTPException(status_code=400, detail={"error": "Contracts folder not found"})

            return StreamingResponse(StreamFileHelper().generate(contracts_dir), media_type="application/json")
        except Exception as e:
            raise e
    
    def file_open(self, relative_path: str):
        file_path = self.CLI_DIR_PATH / "contracts" / relative_path
        if not file_path.exists() or not file_path.is_file():
            return {"error": "File not found"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
        
    def create_solidity_contract(self, file_name: str) -> str:
        try:
            contracts_dir = self.CLI_DIR_PATH / "contracts"
            contracts_dir.mkdir(parents=True, exist_ok=True)

            file_path = contracts_dir / file_name

            if file_path.exists():
                return f"[Info] File '{file_name}' already exists."

            file_path.write_text(StreamFileHelper().solidity_code())

            build_command = (
                "cd " + str(contracts_dir) + " && ./resolc --solc ./solc-static-linux " + file_name +
                " -O3 --bin --output-dir ./build"
            )

            build_proc = subprocess.Popen(
                build_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in build_proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()

            build_proc.wait()
            if build_proc.returncode != 0:
                return "[Build Error] Failed to build contract. Check logs above."

            return f"\n[Success] Contract '{file_name}' created and built successfully."
        except Exception as e:
            raise e
    
    # This comment is to create rust contract using this command cargo contract new {contract_name} ///
    # def create_rust_contract(self, contract_name: str) -> str:
    #     try:
    #         ssh_base = (
    #             f"sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} "
    #             f"{self.ssh_user}@{self.ssh_host}"
    #         )

    #         create_command = (
    #             f"{ssh_base} "
    #             f"\"source ~/.cargo/env && cd ~/contracts && cargo contract new {contract_name}\""
    #         )

    #         create_proc = subprocess.Popen(
    #             create_command,
    #             shell=True,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.STDOUT,
    #             text=True
    #         )

    #         for line in create_proc.stdout:
    #             sys.stdout.write(line)
    #             sys.stdout.flush()

    #         create_proc.wait()
    #         if create_proc.returncode != 0:
    #             return "[Create Error] Failed to create contract. Check logs above."

    #         build_command = (
    #             f"{ssh_base} "
    #             f"\"source ~/.cargo/env && cd ~/contracts/{contract_name} && cargo contract build\""
    #         )

    #         build_proc = subprocess.Popen(
    #             build_command,
    #             shell=True,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.STDOUT,
    #             text=True
    #         )

    #         for line in build_proc.stdout:
    #             sys.stdout.write(line)
    #             sys.stdout.flush()

    #         build_proc.wait()
    #         if build_proc.returncode != 0:
    #             return "[Build Error] Failed to build contract. Check logs above."

    #         return f"\n[Success] Contract '{contract_name}' created and built successfully."
    #     except Exception as e:
    #         raise e

    def create_rust_contract(self, contract_name: str) -> str:
        try:
            contracts_dir = self.CLI_DIR_PATH / "contracts/rust-contract-template"
            os.environ['PATH'] = f"/home/pc/.cargo/bin:{os.environ.get('PATH')}"
            
            build_command = (
                f"cd {contracts_dir} && "
                f"cargo +nightly build --release -Z build-std=core,alloc "
                f"--target={contracts_dir}/riscv64emac-unknown-none-polkavm.json"
            )
 
            build_proc = subprocess.Popen(
                build_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in build_proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()

            build_proc.wait()
            if build_proc.returncode != 0:
                return "[Build Error] Failed to build contract. Check logs above."
 
            contract_binary_path = os.path.join(contracts_dir, "target/riscv64emac-unknown-none-polkavm/release/contract")
            if not os.path.isfile(contract_binary_path):
                return f"[Error] Contract binary not found at {contract_binary_path}. Please ensure the build was successful."
 
            build_result = (
                f"cd {contracts_dir} && "
                f"polkatool link --strip --output {contract_name} {contract_binary_path}"
            )
 
            result_proc = subprocess.Popen(
                build_result,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            result_output = []
            for line in result_proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
 
            result_proc.wait()
            if result_proc.returncode != 0:
                return f"[Link Error] Linking failed:\n{''.join(result_output)}"
 
            return f"[Success] Contract '{contract_name}' build successfully."
        except Exception as e:
            raise e

    def extract_solidity_filename(self, command: str) -> str | None:
        match = re.search(r"([\w\d_-]+\.sol)", command)
        return match.group(1) if match else None


    def command_execute(self, command: str) -> str:
       try:
           file_name = self.extract_solidity_filename(command)
           if file_name:
               create_result = self.create_solidity_contract(file_name)
               return create_result

       # This Comment is to deploy rust using command cargo contract new ///
            # if command.startswith("cargo contract new"):
            #     parts = command.split()
            #     if len(parts) == 4:
            #         contract_name = parts[-1]
            #         return self.create_rust_contract(contract_name)

           if command.startswith("polkatool"):
                parts = command.split()
                if len(parts) == 6:
                    contract_name = parts[-2]
                    return self.create_rust_contract(contract_name)
                
           cli_command = f"cd {self.CLI_DIR_PATH} && {command}"

           result = subprocess.run(
               cli_command,
               shell=True,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True
           )
           if result.returncode != 0:
               return f"[Error]\n{result.stderr.strip()}"
           
           return result.stdout.strip() or "[Success] Command executed but returned no output."
       except Exception as e:
           raise e
       
    def deploy_pvm_contract(self, pvm_file: str):
        try:
            pvm_path = self.CLI_DIR_PATH / "contracts/build" / pvm_file
            if not pvm_path.exists():
                return {"error": f"Bytecode file '{pvm_file}' not found."}

            with open(pvm_path, 'rb') as f:
                bytecode = f.read().hex()

            sys.stdout.write("[Info] Building contract instance...\n")
            sys.stdout.flush()

            abi = [
                {
                    "inputs": [],
                    "stateMutability": "nonpayable",
                    "type": "constructor"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "num", "type": "uint256"}],
                    "name": "store",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "retrieve",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

            contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)

            sys.stdout.write("[Info] Estimating gas...\n")
            sys.stdout.flush()

            gas_estimate = contract.constructor().estimate_gas({
                "from": self.account.address
            })

            gas_price = self.web3.eth.gas_price

            sys.stdout.write("[Info] Building transaction...\n")
            sys.stdout.flush()

            tx = contract.constructor().build_transaction({
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gas": gas_estimate,
                "gasPrice": gas_price,
                "chainId": self.web3.eth.chain_id,
            })

            sys.stdout.write("[Info] Signing transaction...\n")
            sys.stdout.flush()

            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.PRIVATE_KEY)

            sys.stdout.write("[Info] Sending transaction...\n")
            sys.stdout.flush()

            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            sys.stdout.write("[Info] Waiting for transaction receipt...\n")
            sys.stdout.flush()

            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            sys.stdout.write(f"[Success] Contract deployed at: {tx_receipt.contractAddress}\n")
            sys.stdout.flush()
            
            return {
                "message": "Contract deployed successfully.",
                "contract_address": tx_receipt.contractAddress,
                "transaction_hash": tx_hash.hex(),
                "blocknumber": tx_receipt.blockNumber
            }

        except Exception as e:
            raise e
        
    def deploy_rust_contract(self, polkavm_file: str):
        try:
            polkavm_path = self.CLI_DIR_PATH / "contracts/rust-contract-template" / polkavm_file
            if not polkavm_path.exists():
                return {"error": f"Bytecode file '{polkavm_file}' not found."}
 
            with open(polkavm_path, 'rb') as f:
                bytecode = f.read().hex()
 
            abi = [
                {
                    "inputs": [],
                    "stateMutability": "nonpayable",
                    "type": "constructor"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "num", "type": "uint256"}],
                    "name": "store",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "retrieve",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
 
            contract = self.web3.eth.contract(abi=abi, bytecode=bytecode)
 
            gas_estimate = contract.constructor().estimate_gas({
                "from": self.account.address
            })
 
            gas_price = self.web3.eth.gas_price
 
            tx = contract.constructor().build_transaction({
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gas": gas_estimate,
                "gasPrice": gas_price,
                "chainId": self.web3.eth.chain_id,
            })
 
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                "message": "Contract deployed successfully.",
                "contract_address": tx_receipt.contractAddress,
                "transaction_hash": tx_hash.hex(),
                "blocknumber": tx_receipt.blockNumber
            }
 
        except Exception as e:
            raise e
    
    # This comment is to deploy rust contract using .contract file ///
    # def deploy_rust_contract(self, contract_file: str):
    #     try:
    #         contract_name = contract_file.replace(".contract", "")
    #         contract_dir = f"~/contracts/{contract_name}"
    #         contract_file_path = f"{contract_dir}/target/ink/{contract_file}"

    #         ssh_base = (
    #             f"sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} "
    #             f"{self.ssh_user}@{self.ssh_host}"
    #         )

    #         deploy_command = (
    #             f"{ssh_base} "
    #             f"\"source ~/.cargo/env && "
    #             f"cd {contract_dir} && "
    #             f"cargo contract instantiate "
    #             f"{contract_file_path} "
    #             f"--constructor new --args true "
    #             f"--suri //Alice "
    #             f"--skip-confirm "
    #             f"--execute\""
    #         )

    #         deploy_proc = subprocess.Popen(
    #             deploy_command,
    #             shell=True,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.STDOUT,
    #             text=True
    #         )

    #         output_lines = []
    #         for line in deploy_proc.stdout:
    #             sys.stdout.write(line)
    #             sys.stdout.flush()
    #             output_lines.append(line)

    #         deploy_proc.wait()
    #         full_output = ''.join(output_lines)

    #         if deploy_proc.returncode != 0:
    #             return {"error": full_output.strip()}

    #         return {
    #             "message": "Rust (Ink!) contract deployed successfully.",
    #             "output": full_output.strip()
    #         }

    #     except Exception as e:
    #         raise e
    
    def deploy_contract(self, file_name: str):
        try:
            if file_name.endswith(".polkavm"):
                return self.deploy_rust_contract(file_name)
            elif file_name.endswith(".pvm"):
                return self.deploy_pvm_contract(file_name)
            else:
                return {"error": f"Unsupported contract file format: {file_name}"}
        except Exception as e:
            raise e