from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.models.cli import CLICommand
from src.rules.cli import CLIRule

CLIEndpoint = APIRouter()

@CLIEndpoint.get("/directory/list")
def directory_list():
    try:
        return CLIRule().directory_list()
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@CLIEndpoint.get("/file/open/{file_path:path}")
def file_open(file_path: str):
    try:
        file = CLIRule().file_open(file_path)
        if not file:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "File not found.",
                    "data": None
                },
                headers=None
            )
        
        return FileResponse(file, media_type="application/octet-stream", filename=file.name)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@CLIEndpoint.get("/command/execute")
def command_execute(cli_command: CLICommand):
    try:
        executed_command = CLIRule().command_execute(cli_command)
        if not executed_command:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Something's went wrong!",
                    "data": None
                },
                headers=None
            )
        
        return executed_command
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )