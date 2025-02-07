from pydantic import BaseModel
from datetime import datetime

class BlacklistToken(BaseModel):
    token: str
    created_at: datetime
    updated_at: datetime

class GetBlacklistToken(BaseModel):
    id: str
    token: str

class CreateBlacklistToken(BaseModel):
    token: str