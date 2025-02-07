from fastapi.encoders import jsonable_encoder

from typing import List, Optional
from datetime import datetime

from src.models.blacklist_tokens import ( 
    BlacklistToken, 
    GetBlacklistToken, 
    CreateBlacklistToken 
)

from database.mongodb import MongoDBDatabase

class BlacklistTokensRule:
    def __init__(self):
        self.blacklist_tokens_collection = MongoDBDatabase().get_db()["blacklist_tokens"]
        
    def convert_to_get_blacklist_token(self, blacklist_token) -> GetBlacklistToken:
        blacklist_token["_id"] = str(blacklist_token["_id"])
        return GetBlacklistToken(id=blacklist_token["_id"], **blacklist_token)
        
    def get_blacklist_token(self, token: str) -> Optional[GetBlacklistToken]:
        blacklist_token = self.blacklist_tokens_collection.find_one({ "token": token })
        return self.convert_to_get_blacklist_token(blacklist_token) if blacklist_token else None
        
    def create_blacklist_token(self, data: CreateBlacklistToken)-> Optional[GetBlacklistToken]:
        new_blacklist_token = BlacklistToken(
            token=data.token,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        new_blacklist_token_dict = jsonable_encoder(new_blacklist_token)
        result = self.blacklist_tokens_collection.insert_one(new_blacklist_token_dict)

        if result.acknowledged:
            blacklist_token = self.get_blacklist_token(str(result.inserted_id))
            return self.convert_to_get_blacklist_token(blacklist_token) if blacklist_token else None
        return None
    