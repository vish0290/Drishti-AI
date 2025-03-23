from pymongo import MongoClient
from dotenv import load_dotenv
import os
import hashlib
from datetime import datetime
from typing import Dict, Any

load_dotenv()

db_url = os.getenv("DB_URI")
db_name = os.getenv("DB_NAME")
coll_name = os.getenv("USER_COLLECTION")

class UserManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                self.client = MongoClient(db_url)
                self.db = self.client[db_name]
                self.collection = self.db[coll_name]
                self.collection.create_index("username", unique=True)
                self.collection.create_index("email", unique=True)
                self.collection.create_index("api_key")
                self._initialized = True
            except Exception as e:
                print(f"Database initialization error: {str(e)}")
                raise
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_api_key(self, username: str) -> str:
        secret = os.getenv("API_KEY_SECRET", "default_secret")
        key_base = f"{username}:{secret}:{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(key_base.encode()).hexdigest()
    
    def add_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        try:
            # Check if user already exists
            if self.collection.find_one({"$or": [{"username": username}, {"email": email}]}):
                return {
                    "success": False,
                    "message": "Username or email already exists"
                }
            
            # Create user document with hashed password
            api_key = self._generate_api_key(username)
            user_doc = {
                "username": username,
                "password_hash": self._hash_password(password),
                "email": email,
                "api_key": api_key,
                "created_at": datetime.now(),
                "last_login": None
            }
            
            # Insert the user
            self.collection.insert_one(user_doc)
            
            return {
                "success": True,
                "message": "User created successfully",
                "api_key": api_key
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating user: {str(e)}"
            }
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        try:
            # Find the user
            user = self.collection.find_one({"username": username})
            if not user:
                return {
                    "success": False,
                    "message": "User not found"
                }
            
            # Check password
            password_hash = self._hash_password(password)
            if password_hash != user.get("password_hash"):
                return {
                    "success": False,
                    "message": "Invalid password"
                }
                
            # Update last login time
            self.collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "last_login": datetime.now()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Authentication successful",
                "api_key": user.get("api_key"),
                "username": user["username"],
                "email": user["email"]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Authentication error: {str(e)}"
            }
    
    def check_api_key(self, api_key: str) -> Dict[str, Any]:
        try:
            # Find user with this API key
            user = self.collection.find_one({"api_key": api_key})
            if not user:
                return {
                    "success": False,
                    "message": "Invalid API key"
                }
            
            # Return user info
            return {
                "success": True,
                "message": "API key is valid",
                "user_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error checking API key: {str(e)}"
            }
    
    def update_user(self, username: str, password: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # First authenticate the user
            auth_result = self.authenticate_user(username, password)
            if not auth_result["success"]:
                return auth_result
            
            # Prepare update fields
            update_fields = {}
            
            # Handle each field that can be updated
            if "email" in update_data:
                # Check if email already exists for another user
                existing = self.collection.find_one({
                    "email": update_data["email"],
                    "username": {"$ne": username}
                })
                if existing:
                    return {
                        "success": False,
                        "message": "Email already in use by another account"
                    }
                update_fields["email"] = update_data["email"]
            
            if "new_password" in update_data:
                update_fields["password_hash"] = self._hash_password(update_data["new_password"])
            
            # Add any additional fields that are allowed to be updated
            allowed_fields = ["first_name", "last_name", "profile_picture"]
            for field in allowed_fields:
                if field in update_data:
                    update_fields[field] = update_data[field]
            
            # Update the user
            if update_fields:
                self.collection.update_one(
                    {"username": username},
                    {"$set": update_fields}
                )
                
                return {
                    "success": True,
                    "message": "User information updated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "No valid fields to update"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating user: {str(e)}"
            }
    
    def delete_user(self, username: str, password: str) -> Dict[str, Any]:
        try:
            # First authenticate the user
            auth_result = self.authenticate_user(username, password)
            if not auth_result["success"]:
                return auth_result
            
            # Delete the user
            self.collection.delete_one({"username": username})
            
            return {
                "success": True,
                "message": "User account deleted successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error deleting user: {str(e)}"
            }
    
    def close_connection(self):
        """Close the MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()



