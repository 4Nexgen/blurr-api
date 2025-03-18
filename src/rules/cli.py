from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from eth_account import Account

import json
from web3 import Web3
import shlex 

import subprocess
import re

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

    def stream_directory(self, directory: Path):
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Provided path is not a valid directory: {directory}")

        for item in directory.iterdir():
            if item.is_dir():
                yield {
                    "name": item.name,
                    "is_dir": True,
                    "children": list(self.stream_directory(item))
                }
                continue

            yield {
                "name": item.name,
                "is_dir": False,
                "url": f"/{item.relative_to(self.CLI_DIR_PATH)}"
            }
    
    def directory_list(self) -> StreamingResponse:
        try:
            contracts_dir = self.CLI_DIR_PATH / "contracts"

            print("directory path", contracts_dir)
            
            if not contracts_dir.exists() or not contracts_dir.is_dir():
                raise HTTPException(status_code=400, detail={"error": "Contracts folder not found"})

            return StreamingResponse(
                iter([
                    '[',
                    json.dumps({
                        "name": "contracts",
                        "is_dir": True,
                        "children": list(self.stream_directory(contracts_dir))
                    }),
                    ']'
                ]),
                media_type="application/json"
            )
        except Exception as e:
            raise e
    
    def file_open(self, relative_path: str):
        file_path = self.CLI_DIR_PATH / "contracts" / relative_path
        if not file_path.exists() or not file_path.is_file():
            return {"error": "File not found"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
        
    def create_solidity_file(self, file_name: str) -> str:
        solidity_code = """// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

/**
* @title Storage
* @dev Store & retrieve value in a variable
* @custom:dev-run-script ./scripts/deploy_with_ethers.ts
*/
contract Storage {

    uint256 number;

    /**
    * @dev Store value in variable
    * @param num value to store
    */
    function store(uint256 num) public {
        number = num;
    }

    /**
    * @dev Return value 
    * @return value of 'number'
    */
    function retrieve() public view returns (uint256){
        return number;
    }
}
"""
        try:
            contracts_dir = self.CLI_DIR_PATH / "contracts"
            contracts_dir.mkdir(parents=True, exist_ok=True)

            file_path = contracts_dir / file_name

            if file_path.exists():
                return f"[Info] File '{file_name}' already exists."

            file_path.write_text(solidity_code)

            build_command = (
                "cd " + str(contracts_dir) + " && ./resolc --solc ./solc-static-linux " + file_name +
                " -O3 --bin --output-dir ./build"
            )

            build_result = subprocess.run(
                build_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if build_result.returncode != 0:
                return f"[File Created]\nBut build failed:\n{build_result.stderr.strip()}"

            return f"[Success] File '{file_name}' created and built successfully.\n{build_result.stdout.strip()}"

        except Exception as e:
            return f"[Exception] Failed to create and build file: {str(e)}"
    
    def create_rust_contract(self, contract_name: str) -> str:
        try:
            ssh_base = (
                f"sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} "
                f"{self.ssh_user}@{self.ssh_host}"
            )

            create_command = (
                f"{ssh_base} "
                f"\"source ~/.cargo/env && cd ~/contracts && cargo contract new {contract_name}\""
            )

            result_create = subprocess.run(
                create_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result_create.returncode != 0:
                return f"[Create Error]\n{result_create.stderr.strip()}"

            build_command = (
                f"{ssh_base} "
                f"\"source ~/.cargo/env && cd ~/contracts/{contract_name} && cargo contract build\""
            )

            result_build = subprocess.run(
                build_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result_build.returncode != 0:
                return f"[Build Error]\n{result_build.stderr.strip()}"

            return (
                f"[Success] Contract '{contract_name}' created and built successfully.\n\n"
                f"{result_build.stdout.strip()}"
            )

        except Exception as e:
            return f"[Exception] {str(e)}"

        
    def extract_solidity_filename(self, command: str) -> str | None:
        match = re.search(r"([\w\d_-]+\.sol)", command)
        return match.group(1) if match else None

    def command_execute(self, command: str) -> str:
        try:
            file_name = self.extract_solidity_filename(command)

            if file_name:
                create_result = self.create_solidity_file(file_name)
                return create_result

            if command.startswith("cargo contract new"):
                parts = command.split()
                if len(parts) == 4:
                    contract_name = parts[-1]
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
            return f"[Exception] {str(e)}"
        
    def deploy_pvm_contract(self, pvm_file: str):
        try:
            pvm_path = self.CLI_DIR_PATH / "contracts/build" / pvm_file
            if not pvm_path.exists():
                return {"error": f"Bytecode file '{pvm_file}' not found."}

            with open(pvm_path, 'rb') as f:
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
            return {"error": str(e)}
    
    def deploy_rust_contract(self, contract_file: str):
        try:
            contract_name = contract_file.replace(".contract", "")
            contract_dir = f"~/contracts/{contract_name}"
            contract_file_path = f"{contract_dir}/target/ink/{contract_file}"

            ssh_base = (
                f"sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} "
                f"{self.ssh_user}@{self.ssh_host}"
            )

            deploy_command = (
                f"{ssh_base} "
                f"\"source ~/.cargo/env && "
                f"cd {contract_dir} && "
                f"cargo contract instantiate "
                f"{contract_file_path} "
                f"--constructor new --args true "
                f"--suri //Alice "
                f"--skip-confirm "
                f"--execute\""
            )

            result = subprocess.run(
                deploy_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                return {"error": result.stderr.strip()}

            return {
                "message": "Rust (Ink!) contract deployed successfully.",
                "output": result.stdout.strip()
            }

        except Exception as e:
            return {"error": str(e)}
    
    def deploy_contract(self, file_name: str):
        try:
            if file_name.endswith(".contract"):
                return self.deploy_rust_contract(file_name)
            elif file_name.endswith(".pvm"):
                return self.deploy_pvm_contract(file_name)
            else:
                return {"error": f"Unsupported contract file format: {file_name}"}
        except Exception as e:
            return {"error": str(e)}