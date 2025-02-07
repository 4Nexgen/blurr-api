from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from starlette.middleware.sessions import SessionMiddleware

from routes.api import APIRoutes, Routes
from database.mongodb import MongoDBDatabase

secret_key = "personal-life-biography-chatbot-api"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

Routes().load_routes()
app.include_router(APIRoutes)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Blurr API",
        version="1.0.1",
        summary="Blurr API is a powerful backend service that allows developers to compile, deploy, and interact with Solidity and Rust smart contracts on Substrate-based blockchains. It integrates seamlessly with the Blurr browser-based IDE, enabling efficient smart contract development and deployment.",
        description="Blurr API provides a robust set of endpoints for compiling contracts, deploying them to Substrate-based networks, executing contract calls, and querying blockchain states. Designed for efficiency and scalability, it simplifies the development process by offering secure key management, event monitoring, and seamless blockchain interactions.",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

MongoDBDatabase().load_db()