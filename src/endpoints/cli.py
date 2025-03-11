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

@CLIEndpoint.websocket("/connect-socket/")
async def command_execute(websocket: WebSocket):
    await websocket.accept()
    socket_id = str(uuid.uuid1())
    active_websockets[socket_id] = websocket

    try:
        while True:
            try:
                raw_data = await websocket.receive_text()
                parsed = json.loads(raw_data)

                command = parsed.get("command", "").strip()
                create_sol = parsed.get("create_sol", False)

                if not command and not create_sol:
                    await websocket.send_text(json.dumps({
                        "message": "No command provided"
                    }))
                    continue

                result = CLIRule().command_execute(command, create_sol=create_sol)

                await websocket.send_text(json.dumps({
                    "message": "Command executed",
                    "output": result
                }))

            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "message": "Invalid JSON format",
                    "error": str(e)
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "message": "Command execution error",
                    "error": str(e)
                }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "message": "Internal Server Error",
            "error": str(e)
        }))
    finally:
        active_websockets.pop(socket_id, None)

@CLIEndpoint.websocket("/connect-socket/deploy/")
async def deploy_contract_ws(websocket: WebSocket):
    await websocket.accept()

    socket_id = str(uuid.uuid1())
    active_websockets[socket_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            contract_language = payload.get("language")
            file_name = payload.get("file_name")
            contract_code = payload.get("code")

            if contract_language == "solidity":
                result = CLIRule().deploy_solidity(file_name, contract_code)
            # elif contract_language == "rust":
            #     result = deploy_rust(file_name, contract_code)
            else:
                result = "[Error] Unknown contract language."

            await websocket.send_text(result)

    except Exception as e:
        await websocket.send_text(json.dumps({
            "message": "Internal Server Error",
            "error": str(e)
        }))
    finally:
        active_websockets.pop(socket_id, None)