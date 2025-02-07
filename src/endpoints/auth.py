from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from src.models.auth import GoogleUser
from src.rules.auth import AuthRule, authenticate_user

AuthEndpoint = APIRouter()

@AuthEndpoint.get("/get_user/by_token/{token}")
def get_user_by_token(token: str, _ = Depends(authenticate_user)):
    try:
        user_data = AuthRule().get_user_by_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "User not found.",
                    "data": None
                },
                headers=None
            )
        
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@AuthEndpoint.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    auth_rule = AuthRule()
    
    user = auth_rule.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "User account is disabled.",
                "data": None
            }
        )
    
    access_token_expires = timedelta(minutes=60)
    access_token = auth_rule.create_access_token(
        data={"sub": user.email}, 
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

@AuthEndpoint.post("/google")
async def login_using_google(data: GoogleUser):
    try:
        result = AuthRule().login_using_google(data)
        if not result:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Something went wrong.", 
                    "data": None
                }
            )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )
    
@AuthEndpoint.post("/logout")
def logout(token: str = Depends(AuthRule().get_current_token)):
    is_logout = AuthRule().logout(token)
    if is_logout:
        return True
    return None