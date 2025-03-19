from fastapi import APIRouter, HTTPException, WebSocket
from fastapi.responses import FileResponse

from src.rules.cli import CLIRule

import uuid
import json

from typing import Dict

CLIEndpoint = APIRouter()

active_websockets: Dict[str, WebSocket] = {}


@CLIEndpoint.get("/directory/list")
def directory_list():
    try:
        directory_list = CLIRule().directory_list()

        if not directory_list:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "File not found.",
                    "data": None
                },
                headers=None
            )
        
        return directory_list
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
        
        return file
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@CLIEndpoint.websocket("/connect-socket/")
async def command_execute(websocket: WebSocket):
    await websocket.accept()
    socket_id = str(uuid.uuid1())
    active_websockets[socket_id] = websocket

    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                parsed = json.loads(raw_data)
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "message": "Invalid JSON format",
                    "error": str(e)
                }))
                continue

            command = parsed.get("command", "").strip()
            if not command:
                await websocket.send_text(json.dumps({
                    "message": "No command provided"
                }))
                continue

            execution_result = CLIRule().command_execute(command)

            if command.endswith((".pvm", ".contract")):
                deploy_result = CLIRule().deploy_contract(command)

                if deploy_result:
                    await websocket.send_text(json.dumps({
                        "status": "success",
                        "message": "Contract deployed successfully",
                        "deploy_output": deploy_result
                    }))
                    continue

            await websocket.send_text(json.dumps({
                "status": "success",
                "message": "Command executed",
                "command_output": execution_result
            }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "message": "Internal Server Error",
            "error": str(e)
        }))
    finally:
        active_websockets.pop(socket_id, None)
