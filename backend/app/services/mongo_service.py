"""
MongoDB Persistence Service for research job analysis documents.
Provides asynchronous CRUD operations using Motor.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_research_collection

logger = logging.getLogger(__name__)


class MongoService:
    """
    Singleton persistence service managing research analysis documents in MongoDB Atlas.
    """

    _instance: Optional["MongoService"] = None

    def __new__(cls) -> "MongoService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def _get_collection() -> AsyncIOMotorCollection:
        """Helper to obtain the configured Motor collection instance."""
        return get_research_collection()

    @staticmethod
    def _serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Converts BSON ObjectId and non-serializable types into JSON-friendly formats.
        """
        if doc is None:
            return None

        result = dict(doc)
        if "_id" in result and isinstance(result["_id"], ObjectId):
            result["_id"] = str(result["_id"])
        return result

    async def create_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserts a new research analysis document into the collection.

        Args:
            analysis_data: Document dictionary containing job_id, user_query, etc.

        Returns:
            Dict[str, Any]: Inserted document dictionary with string _id.
        """
        if not analysis_data or not isinstance(analysis_data, dict):
            raise ValueError("analysis_data must be a non-empty dictionary.")

        job_id = analysis_data.get("job_id")
        if not job_id or not isinstance(job_id, str):
            raise ValueError("analysis_data must contain a valid string 'job_id'.")

        collection = self._get_collection()

        doc_to_insert = dict(analysis_data)
        if "created_at" not in doc_to_insert:
            doc_to_insert["created_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Inserting research analysis document: job_id='{job_id}'")

        try:
            result = await collection.insert_one(doc_to_insert)
            doc_to_insert["_id"] = str(result.inserted_id)
            logger.info(f"Successfully created research analysis document (id={doc_to_insert['_id']}).")
            return doc_to_insert
        except Exception as e:
            logger.error(f"Failed to insert research analysis document job_id='{job_id}': {e}", exc_info=True)
            raise RuntimeError(f"Database insert failed for job_id '{job_id}': {str(e)}") from e

    async def get_analysis_by_job_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a research analysis document by job_id.

        Args:
            job_id: Unique research analysis job identifier.

        Returns:
            Optional[Dict[str, Any]]: Document dict or None if not found.
        """
        if not job_id or not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string.")

        clean_id = job_id.strip()
        collection = self._get_collection()

        logger.info(f"Fetching research analysis document: job_id='{clean_id}'")

        try:
            doc = await collection.find_one({"job_id": clean_id})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.error(f"Failed to fetch analysis document job_id='{clean_id}': {e}", exc_info=True)
            raise RuntimeError(f"Database query failed for job_id '{clean_id}': {str(e)}") from e

    async def update_analysis(self, job_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates an existing research analysis document by job_id.

        Args:
            job_id: Unique research analysis job identifier.
            update_data: Fields to update via $set operator.

        Returns:
            Optional[Dict[str, Any]]: Updated document or None if not found.
        """
        if not job_id or not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string.")

        if not update_data or not isinstance(update_data, dict):
            raise ValueError("update_data must be a non-empty dictionary.")

        clean_id = job_id.strip()
        collection = self._get_collection()

        fields_to_set = {k: v for k, v in update_data.items() if k != "_id"}
        fields_to_set["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Updating research analysis document: job_id='{clean_id}'")

        try:
            updated_doc = await collection.find_one_and_update(
                {"job_id": clean_id},
                {"$set": fields_to_set},
                return_document=True,
            )
            return self._serialize_doc(updated_doc)
        except Exception as e:
            logger.error(f"Failed to update analysis document job_id='{clean_id}': {e}", exc_info=True)
            raise RuntimeError(f"Database update failed for job_id '{clean_id}': {str(e)}") from e

    async def update_status(
        self,
        job_id: str,
        status: str,
        errors: Optional[List[str]] = None,
    ) -> bool:
        """
        Updates the status and optional error messages for a research analysis job.

        Args:
            job_id: Unique research job identifier.
            status: New status string (e.g. 'processing', 'completed', 'failed').
            errors: Optional list of error strings.

        Returns:
            bool: True if document was updated, False if job_id was not found.
        """
        if not job_id or not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string.")

        if not status or not isinstance(status, str):
            raise ValueError("status must be a non-empty string.")

        clean_id = job_id.strip()
        collection = self._get_collection()

        update_payload: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if status == "completed":
            update_payload["completed_at"] = datetime.now(timezone.utc).isoformat()

        if errors is not None:
            update_payload["errors"] = errors

        try:
            result = await collection.update_one(
                {"job_id": clean_id},
                {"$set": update_payload},
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            logger.error(f"Failed to update status for job_id='{clean_id}': {e}", exc_info=True)
            raise RuntimeError(f"Status update failed for job_id '{clean_id}': {str(e)}") from e

    async def delete_analysis(self, job_id: str) -> bool:
        """
        Deletes a research analysis document by job_id.

        Args:
            job_id: Unique research analysis job identifier.

        Returns:
            bool: True if document was deleted, False if not found.
        """
        if not job_id or not isinstance(job_id, str) or not job_id.strip():
            raise ValueError("job_id must be a non-empty string.")

        clean_id = job_id.strip()
        collection = self._get_collection()

        logger.info(f"Deleting research analysis document: job_id='{clean_id}'")

        try:
            result = await collection.delete_one({"job_id": clean_id})
            deleted = result.deleted_count > 0
            if deleted:
                logger.info(f"Successfully deleted document job_id='{clean_id}'.")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete document job_id='{clean_id}': {e}", exc_info=True)
            raise RuntimeError(f"Database delete failed for job_id '{clean_id}': {str(e)}") from e


# Singleton instance export
mongo_service = MongoService()


def get_mongo_service() -> MongoService:
    """
    Returns the singleton MongoService instance.
    """
    return mongo_service
