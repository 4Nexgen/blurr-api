from pathlib import Path

import subprocess
import re

import os
from dotenv import load_dotenv
load_dotenv()

class CLIRule:
    def __init__(self):
        self.CLI_DIR_PATH = Path(os.getenv("CLI_DIR")) 
    
    def build_tree(self, directory: Path):
        tree = {"name": directory.name, "is_dir": True, "children": []}
        
        for item in directory.iterdir():
            if item.is_dir():
                tree["children"].append(self.build_tree(item)) 
            else:
                tree["children"].append({"name": item.name, "is_dir": False, "url": f"/{item.relative_to(self.CLI_DIR_PATH)}"})
        
        return tree
    
    def directory_list(self):
        if not self.CLI_DIR_PATH.exists() or not self.CLI_DIR_PATH.is_dir():
            return {"error": "Invalid base directory"}
        
        return self.build_tree(self.CLI_DIR_PATH)
    
    def file_open(self, file_path: str):
        if file_path.startswith('/'):
            file_path = file_path[1:]

        file = self.CLI_DIR_PATH.joinpath(file_path)

        if not file.exists() or not file.is_file():
            return None
        
        return file
    
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
                f"cd {contracts_dir} && ./resolc --solc ./solc-static-linux {file_name} "
                f"-O3 --bin --output-dir ./build"
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

    def extract_solidity_filename(self, command: str) -> str | None:
        match = re.search(r"([\w\d_-]+\.sol)", command)
        return match.group(1) if match else None

    def command_execute(self, command: str, create_sol: bool = False) -> str:
        try:
            file_name = self.extract_solidity_filename(command) if create_sol else None

            if create_sol:
                if not file_name:
                    return "[Error] No `.sol` file found in the command."
                return self.create_solidity_file(file_name)

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
        
    def deploy_solidity(self, file_name: str, code: str) -> str:
        try:
            remote_path = f"{self.remote_home}/contracts/{file_name}"

            ssh_command = (
                f"sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} "
                f"{self.ssh_user}@{self.ssh_host} "
                f"\"cat > {remote_path} << 'EOF'\n{code}\nEOF\""
            )

            subprocess.run(ssh_command, shell=True, check=True)

            build_command = f"""sshpass -p '{self.ssh_password}' ssh -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} "cd {self.remote_home}/contracts && ./resolc --solc ./solc-static-linux {file_name} -O3 --bin --output-dir ./build/" """
            result = subprocess.run(build_command, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                return f"[Error - Solidity Build]\n{result.stderr.strip()}"

            return f"[Solidity Compiled Successfully]\n{result.stdout.strip()}"

        except Exception as e:
            return f"[Exception - Solidity Deploy] {str(e)}"