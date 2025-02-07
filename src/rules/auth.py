from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

from src.models.users import User, GetUser
from src.models.auth import TokenData, GoogleUser
from src.models.users import CreateUser
from src.models.blacklist_tokens import CreateBlacklistToken
from src.rules.users import UsersRule
from src.rules.blacklist_tokens import BlacklistTokensRule

import hashlib
import requests

import os
from dotenv import load_dotenv
load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRule:
    def __init__(self):
        self.AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
        self.AUTH_ALGORITHM = os.getenv("AUTH_ALGORITHM")
        self.AUTH_TOKEN_EXPIRATION = os.getenv("AUTH_TOKEN_EXPIRATION")
        
        self.GOOGLE_OAUTH2_URL = os.getenv("GOOGLE_OAUTH2_URL")

    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_user(self, identifier: str):
        user = UsersRule().get_auth_user_by_email(identifier)
        if not user:
            user = UsersRule().get_auth_user_by_username(identifier)
        return user

    def authenticate_user(self, identifier: str, password: str):
        user = self.get_user(identifier)
        if user:
            if not self.verify_password(password, user.hashed_password):
                return False
        return user
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(days=float(self.AUTH_TOKEN_EXPIRATION))

        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.AUTH_SECRET_KEY, algorithm=self.AUTH_ALGORITHM)
        except JWTError as e:
            raise Exception("Error encoding JWT token") from e

        return encoded_jwt

    async def get_current_token(self, token: str = Depends(oauth2_scheme)) -> str:
        if token:
            return token
        return None

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        blacklist_token = BlacklistTokensRule().get_blacklist_token(token)
        if blacklist_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been invalidated.")

        try:
            payload = jwt.decode(token, self.AUTH_SECRET_KEY, algorithms=self.AUTH_ALGORITHM)
            identifier: str = payload.get("sub")
            
            if identifier is None:
                raise credentials_exception
            
            token_data = TokenData(identifier=identifier)
        except JWTError:
            raise credentials_exception
        
        user = self.get_user(identifier=token_data.identifier)
        
        if user is None:
            raise credentials_exception
        return user
    
    def get_user_by_token(self, token: str) -> Optional[GetUser]:
        payload = jwt.decode(token, self.AUTH_SECRET_KEY, algorithms=[self.AUTH_ALGORITHM])
        
        identifier: str = payload.get("sub")
        token_data = TokenData(identifier=identifier)
        
        user_by_identifier = self.get_user(identifier=token_data.identifier)
        
        if user_by_identifier:
            user = UsersRule().get_user(user_by_identifier.id)
            return user if user else None
        return None

    def validate_access_token(self, access_token):
        try:
            response = requests.get(f"{self.GOOGLE_OAUTH2_URL}{access_token}")
            id_info = response.json()
            return id_info
        except ValueError as e:
            raise Exception(f"Token validation failed: {e}")
        
    def login_using_google(self, data: GoogleUser):
        id_info = self.validate_access_token(data.access_token)
        sub = id_info.get('sub')
        
        if sub != data.google_account_id:
            return None
        
        combined_value = data.email + data.google_account_id
        password = hashlib.sha256(combined_value.encode()).hexdigest()

        user = UsersRule().get_user_by_google_account_id(data.google_account_id)
        if user:
            if user.email == data.email:
                try:
                    if self.authenticate_user(data.email, password):
                        access_token_expires = timedelta(days=float(self.AUTH_TOKEN_EXPIRATION))
                        access_token = self.create_access_token(
                            data={"sub": data.email}, 
                            expires_delta=access_token_expires
                        )

                        return {
                            "access_token": access_token,
                            "token_type": "bearer",
                            "user": {
                                "full_name": user.full_name,
                                "email": user.email,
                                "username": user.username,
                                "photo_url": user.photo_url
                            }
                        }
                except Exception as e:
                    print(f"An error occurred: {e}")

            return None
            
        new_user = CreateUser(
            full_name=data.full_name,
            email=data.email,
            username=data.email,
            password=password,
            confirm_password=password,
            disabled=False, 
            type="public",
            photo_url=data.photo_url,
            google_account_id=data.google_account_id
        )

        create_user = UsersRule().create_user(new_user)
        if create_user:
            try:
                access_token_expires = timedelta(days=float(self.AUTH_TOKEN_EXPIRATION))
                access_token = self.create_access_token(
                    data={"sub": data.email}, 
                    expires_delta=access_token_expires
                )
                
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "user": {
                        "full_name": data.full_name,
                        "email": data.email,
                        "username": data.email,
                        "photo_url": data.photo_url
                    }
                }
            except Exception as e:
                print(f"An error occurred: {e}")
            
        return None
    
    def logout(self, token: str):
        new_blacklist_token = CreateBlacklistToken(token=token)
        
        existing_blacklist_token = BlacklistTokensRule().get_blacklist_token(new_blacklist_token.token)
        if existing_blacklist_token:
            return True
        
        blacklist_token = BlacklistTokensRule().create_blacklist_token(new_blacklist_token)
        if blacklist_token:
            return True
        return None

def authenticate_user(current_user: dict = Depends(AuthRule().get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return current_user