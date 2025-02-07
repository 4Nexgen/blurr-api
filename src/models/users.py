from pydantic import BaseModel, SecretStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    full_name: str
    email: str
    username: str
    hashed_password: str
    disabled: bool = False
    type: str
    google_account_id: Optional[str] = None
    photo_url: str
    created_at: datetime
    updated_at: datetime

class GetUser(BaseModel):
    id: str
    full_name: str
    email: str
    username: str
    disabled: bool
    type: str
    photo_url: str
    created_at: datetime
    updated_at: datetime

class CreateUser(BaseModel):
    full_name: str
    email: str
    username: str
    password: SecretStr 
    confirm_password: SecretStr
    disabled: bool = False
    type: str
    photo_url: str
    google_account_id: Optional[str] = None
    
class UpdateUser(BaseModel):
    full_name: str
    
class GetAuthUser(BaseModel):
    id: str
    full_name: str
    email: str
    username: str
    hashed_password: str
    disabled: bool = False
    type: str
    photo_url: str
    google_account_id: Optional[str] = None