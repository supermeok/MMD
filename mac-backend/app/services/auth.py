import hashlib
import secrets
import time
import uuid
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

from app.config import Settings


class AuthService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = MongoClient(settings.mongo_uri)
        self.db = self.client[settings.mongo_db]
        self.users = self.db["users"]
        self.tokens = self.db["tokens"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self.users.create_index("username", unique=True)
        self.tokens.create_index("token", unique=True)
        self.tokens.create_index("expires_at", expireAfterSeconds=0)

    def close(self):
        self.client.close()

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_hex(32)

    def register(self, username: str, password: str) -> dict:
        existing = self.users.find_one({"username": username})
        if existing:
            raise ValueError("用户名已存在")

        user_doc = {
            "username": username,
            "password_hash": self._hash_password(password),
            "email": "",
            "avatar": "",
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self.users.insert_one(user_doc)
        return {
            "id": str(result.inserted_id),
            "username": username,
            "created_at": user_doc["created_at"],
        }

    def login(self, username: str, password: str) -> dict:
        user = self.users.find_one({"username": username})
        if not user:
            raise ValueError("用户名或密码错误")

        if user["password_hash"] != self._hash_password(password):
            raise ValueError("用户名或密码错误")

        token = self._generate_token()
        expires_at = int(time.time()) + 86400 * 7

        self.tokens.insert_one({
            "token": token,
            "user_id": str(user["_id"]),
            "username": user["username"],
            "expires_at": expires_at,
        })

        return {
            "token": token,
            "username": user["username"],
            "user_id": str(user["_id"]),
        }

    def verify_token(self, token: str) -> dict | None:
        token_doc = self.tokens.find_one({"token": token})
        if not token_doc:
            return None

        if token_doc["expires_at"] < int(time.time()):
            self.tokens.delete_one({"token": token})
            return None

        return {
            "user_id": token_doc["user_id"],
            "username": token_doc["username"],
        }

    def logout(self, token: str) -> bool:
        result = self.tokens.delete_one({"token": token})
        return result.deleted_count > 0

    def get_profile(self, user_id: str) -> dict:
        from bson import ObjectId
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("用户不存在")

        return {
            "id": str(user["_id"]),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "avatar": user.get("avatar", ""),
            "created_at": user.get("created_at", ""),
        }

    def update_profile(self, user_id: str, username: str | None = None, email: str | None = None, password: str | None = None) -> dict:
        from bson import ObjectId
        
        update_fields = {}
        
        if username is not None:
            existing = self.users.find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}})
            if existing:
                raise ValueError("用户名已被使用")
            update_fields["username"] = username
        
        if email is not None:
            update_fields["email"] = email
        
        if password is not None:
            update_fields["password_hash"] = self._hash_password(password)
        
        if update_fields:
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_fields}
            )
        
        return self.get_profile(user_id)

    def update_avatar(self, user_id: str, avatar_file) -> str:
        from bson import ObjectId
        
        avatar_dir = self.settings.storage_dir / "avatars"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = ".png"
        if hasattr(avatar_file, 'filename') and avatar_file.filename:
            ext = Path(avatar_file.filename).suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                file_ext = ext
        
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
        file_path = avatar_dir / filename
        
        content = avatar_file.file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        avatar_url = f"/media/avatars/{filename}"
        
        self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"avatar": avatar_url}}
        )
        
        return avatar_url
