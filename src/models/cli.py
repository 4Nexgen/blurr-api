from pydantic import BaseModel

class CLICommand(BaseModel):
    command: str