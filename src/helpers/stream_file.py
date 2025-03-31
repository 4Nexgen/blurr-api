from pathlib import Path
import json

import os
from dotenv import load_dotenv
load_dotenv()

class StreamFileHelper:
    def __init__(self):
        self.CLI_DIR_PATH = Path(os.getenv("CLI_DIR"))
        self.ALLOWED_EXTENSIONS = {".sol", ".polkavm", ".pvm"}

    def stream_directory(self, directory: Path):
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Provided path is not a valid directory: {directory}")

        children = []
        is_rust_contract_template = directory.name == "rust-contract-template"

        for item in directory.iterdir():
            if item.is_dir():
                sub_children = list(self.stream_directory(item))
                if sub_children: 
                    children.append({
                        "name": item.name,
                        "is_dir": True,
                        "children": sub_children
                    })
            if item.is_file():
                if is_rust_contract_template and item.suffix == ".sol":
                    continue
                
                if item.suffix in self.ALLOWED_EXTENSIONS:
                    children.append({
                        "name": item.name,
                        "is_dir": False,
                        "url": f"/{item.relative_to(self.CLI_DIR_PATH)}"
                    })

        return children

    def generate(self, contracts_dir: Path):
        data = {
            "name": "contracts",
            "is_dir": True,
            "children": list(self.stream_directory(contracts_dir))
        }
        yield json.dumps(data)
        
    def solidity_code(self):
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
        return solidity_code