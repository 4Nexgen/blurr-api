from fastapi import APIRouter, Depends, HTTPException

from src.rules.auth import authenticate_user
from src.rules.users import UsersRule
from src.models.users import ( 
    CreateUser, 
    UpdateUser
)

UsersEndpoint = APIRouter()

@UsersEndpoint.get("")
def get_users(_ = Depends(authenticate_user)):
    try:
        users = UsersRule().get_users()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )
  
@UsersEndpoint.get("/{id}")
def get_user(id: str, _ = Depends(authenticate_user)):
    try:
        user = UsersRule().get_user(id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "User not found.",
                    "data": None
                },
                headers=None
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@UsersEndpoint.post("")
def create_user(data: CreateUser):
    try:
        if data.password != data.confirm_password:
            raise HTTPException(status_code=400, detail={
                "message": "Password and confirm password do not match.",
                "data": None
            })
        
        created_user = UsersRule().create_user(data)
        if not created_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": "Something went wrong.",
                    "data": None
                },
                headers=None
            )
        
        return created_user
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )

@UsersEndpoint.put("/{id}")
def update_user(id: str, data: UpdateUser, _ = Depends(authenticate_user)):
    try:
        user = UsersRule().get_user(id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "User not found.",
                    "data": None
                },
                headers=None
            )
        
        updated_user = UsersRule().update_user(id, data)
        if not updated_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": f"Something's went wrong!",
                    "data": None
                },
                headers=None
            )
        
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )
    
@UsersEndpoint.put("/disable/{id}")
def disable_user(id: str, _ = Depends(authenticate_user)):
    try:
        user = UsersRule().get_user(id)
        if not user:
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": "User not found.",
                    "data": None
                },
                headers=None
            )
            
        disabled_user =  UsersRule().disable_user(id)
        if not disabled_user:
            raise HTTPException(
                status_code=400, 
                detail={
                    "message": f"Something's went wrong!",
                    "data": None
                },
                headers=None
            )
        
        return disabled_user
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "message": f"Internal Server Error: {e}",
                "data": None
            }
        )