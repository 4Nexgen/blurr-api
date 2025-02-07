from pydantic import BaseModel
from pydantic.networks import EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    identifier: str = None

class GoogleUser(BaseModel):
    full_name: str
    email: EmailStr
    google_account_id: str
    photo_url: str
    access_token: str