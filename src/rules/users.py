from fastapi.encoders import jsonable_encoder

from passlib.context import CryptContext
from bson import ObjectId
from typing import List, Optional
from datetime import datetime

from src.models.users import ( 
    User, 
    GetUser, 
    CreateUser, 
    UpdateUser, 
    GetAuthUser 
)

from database.mongodb import MongoDBDatabase

class UsersRule:
    def __init__(self):
        self.users_collection = MongoDBDatabase().get_db()["users"]
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    def convert_to_get_users(self, mongo_cursor) -> List[GetUser]:
        users = []
        for user in mongo_cursor:
            user["_id"] = str(user["_id"])
            user_instance = GetUser(
                id=user["_id"],
                **user
            )
            users.append(user_instance)
        return users

    def convert_to_get_user(self, user) -> GetUser:
        user["_id"] = str(user["_id"])
        return GetUser(id=user["_id"], **user)
        
    def convert_to_get_auth_user(self, user) -> GetAuthUser:
        user["_id"] = str(user["_id"])
        return GetAuthUser(id=user["_id"], **user)
        
    def get_users(self) -> List[GetUser]:
        users = self.users_collection.find()
        return self.convert_to_get_users(users)
        
    def get_user(self, id: str) -> Optional[GetUser]:
        user = self.users_collection.find_one({"_id": ObjectId(id)})
        return self.convert_to_get_user(user) if user else None

    def get_user_by_email(self, email: str) -> Optional[GetUser]:
        user = self.users_collection.find_one({  "email": email })
        return self.convert_to_get_user(user) if user else None

    def get_user_by_username(self, username: str) -> Optional[GetUser]:
        user = self.users_collection.find_one({  "username": username })
        return self.convert_to_get_user(user) if user else None

    def get_user_by_google_account_id(self, google_account_id: str) -> Optional[GetUser]:
        user = self.users_collection.find_one({  "google_account_id": google_account_id })
        return self.convert_to_get_user(user) if user else None
     
    def get_auth_user_by_email(self, email: str) -> Optional[GetAuthUser]:
        user = self.users_collection.find_one({  "email": email })
        return self.convert_to_get_auth_user(user) if user else None

    def get_auth_user_by_username(self, username: str) -> Optional[GetAuthUser]:
        user = self.users_collection.find_one({ "username": username })
        return self.convert_to_get_auth_user(user) if user else None
     
    def create_user(self, data: CreateUser) -> Optional[GetUser]:
        password = data.password.get_secret_value()
        hashed_password = self.pwd_context.hash(password)
        
        register_new_user = User(
            full_name=data.full_name,
            email=data.email,
            username=data.username,
            hashed_password=hashed_password,
            disabled=False,
            type=data.type,
            google_account_id=data.google_account_id,
            photo_url=data.photo_url,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        register_new_user_dict = jsonable_encoder(register_new_user)
        result = self.users_collection.insert_one(register_new_user_dict)
        
        if result.acknowledged:
            return self.get_user(str(result.inserted_id))
        return None
       
    def update_user(self, id: str, data: UpdateUser) -> Optional[GetUser]:
        update_data = {}
        if data.full_name is not None:
            update_data['full_name'] = data.full_name
    
        if not update_data:
            return None 
    
        result = self.users_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if result.modified_count > 0:
            return self.get_user(id)
        
        return None
        
    def disable_user(self, id: str) -> Optional[GetUser]:
        update_data = {}
        update_data['disabled'] = True
    
        if not update_data:
            return None 
    
        result = self.users_collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
        if result.modified_count > 0:
            return self.get_user(id)
        
        return None

    def delete_user(self, id: str) -> bool:
        result = self.users_collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0