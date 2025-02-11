from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId


class MongoDB:
    def __init__(self):
        connection_string = os.getenv("MONGO_CONNECTION_STRING")
        db_name = os.getenv("MONGO_DB_NAME", "gethome-01-hmg")
        self.collection_name = "lots_detections_details_hmg"

        if not connection_string:
            raise ValueError(
                "MONGO_CONNECTION_STRING not found in environment variables"
            )

        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[self.collection_name]

    async def insert_detection(self, detection_data: Dict[str, Any]) -> str:
        """Insert initial detection data and return the document ID"""
        detection_data["created_at"] = datetime.utcnow()
        result = await self.collection.insert_one(detection_data)
        return str(result.inserted_id)

    async def update_detection(
        self, doc_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update existing detection document"""
        result = await self.collection.update_one(
            {"_id": ObjectId(doc_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    async def get_detection(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve detection document"""
        return await self.collection.find_one({"_id": ObjectId(doc_id)})
