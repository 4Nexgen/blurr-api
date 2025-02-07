from pathlib import Path

import os
from dotenv import load_dotenv
load_dotenv()

from src.models.cli import CLICommand

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
    
    def command_execute(str, cli_command: CLICommand):
        return cli_command