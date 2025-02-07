from fastapi import APIRouter
# from src.endpoints.users import UsersEndpoint
# from src.endpoints.auth import AuthEndpoint
from src.endpoints.cli import CLIEndpoint

APIRoutes = APIRouter()

class Routes:
    def load_routes(self):
        # APIRoutes.include_router(UsersEndpoint, prefix="/api/users", tags=["Users"])
        # APIRoutes.include_router(AuthEndpoint, prefix="/api/auth", tags=["Authentication"])
        APIRoutes.include_router(CLIEndpoint, prefix="/api/cli", tags=["CLI"])