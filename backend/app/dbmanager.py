import os
from datetime import datetime, timezone
from typing import Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client, Query
from .schemas.job_app import JobApplication

class DatabaseManager:
    """
    Simplified database manager for JobFinder application using Firestore.
    """

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the database manager with simplified connection logic.

        Args:
            credentials_path: Path to Firebase service account credentials JSON file.
                             Defaults to the databasecreds.json in backend folder.
        """
        self.db: Optional[Client] = None
        self._initialize_firebase(credentials_path)

    def _initialize_firebase(self, credentials_path: Optional[str] = None):
        """Initialize Firebase Admin SDK and Firestore client with simplified logic."""
        try:
            # Check if Firebase is already initialized
            try:
                app = firebase_admin.get_app()
            except ValueError:
                # Firebase not initialized, so initialize it
                # If no credentials path provided, use the default one in backend folder
                if not credentials_path:
                    # Get the directory where this file is located
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    # Go up one level to backend directory
                    backend_dir = os.path.dirname(current_dir)
                    credentials_path = os.path.join(backend_dir, "databasecreds.json")

                print(f"Looking for credentials at: {credentials_path}")

                if credentials_path and os.path.exists(credentials_path):
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred)
                else:
                    raise FileNotFoundError(
                        f"Credentials file not found at {credentials_path}. "
                        f"Please ensure databasecreds.json exists in the backend folder."
                    )

            # Initialize Firestore client
            self.db = firestore.client()
            print("Firestore client initialized successfully!")

        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise

    def _serialize_datetime(self, obj: Any) -> Any:
        """Convert datetime objects to Firestore-compatible format."""
        if isinstance(obj, datetime):
            return obj
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        return obj

    def _deserialize_datetime(self, obj: Any) -> Any:
        """Convert Firestore timestamps back to datetime objects."""
        if hasattr(obj, 'timestamp'):
            # Firestore timestamp
            return obj.timestamp()
        elif isinstance(obj, dict):
            return {k: self._deserialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetime(item) for item in obj]
        return obj

    # Job Application Operations
    async def create_job_application(self, application: JobApplication) -> bool:
        """
        Create a new job application record.

        Args:
            application: JobApplication object to create

        Returns:
            True if created successfully, False otherwise
        """
        try:
            # Convert Pydantic model to dictionary
            data = application.model_dump()

            # Serialize datetime objects
            data = self._serialize_datetime(data)

            self.db.collection('jobs').document(application.application_id).set(data)
            print(f"Job application created: {application.application_id}")
            return True
        except Exception as e:
            print(f"Error creating job application: {e}")
            return False

    async def get_job_application(self, application_id: str) -> Optional[JobApplication]:
        """
        Get a job application by ID.

        Args:
            application_id: The ID of the job application

        Returns:
            JobApplication object if found, None otherwise
        """
        try:
            doc_ref = self.db.collection('jobs').document(application_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data = self._deserialize_datetime(data)
                return JobApplication(**data)
            return None
        except Exception as e:
            print(f"Error getting job application: {e}")
            return None

    async def get_job_by_url(self, job_url: str) -> Optional[JobApplication]:
        """
        Get a job application by job URL.

        Args:
            job_url: The URL of the job posting

        Returns:
            JobApplication object if found, None otherwise
        """
        try:
            query = self.db.collection('jobs').where('job_url', '==', job_url).limit(1)
            docs = query.stream()

            for doc in docs:
                data = doc.to_dict()
                data = self._deserialize_datetime(data)
                return JobApplication(**data)
            return None
        except Exception as e:
            print(f"Error getting job by URL: {e}")
            return None

    async def update_job_application(self, application_id: str, application: JobApplication) -> bool:
        """
        Update an existing job application record.

        Args:
            application_id: ID of the job application to update
            application: JobApplication object with updated data

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Convert Pydantic model to dictionary
            data = application.model_dump()

            # Serialize datetime objects
            data = self._serialize_datetime(data)

            self.db.collection('jobs').document(application_id).set(data, merge=True)
            print(f"Job application updated: {application_id}")
            return True
        except Exception as e:
            print(f"Error updating job application: {e}")
            return False

    async def get_jobs_paginated(self, limit: int = 10, offset: int = 0, order_by: str = "date_posted", order_direction: str = "desc", category: str = None) -> dict:
        """
        Get job applications with pagination support.

        Args:
            limit: Number of jobs to fetch (n)
            offset: Number of jobs to skip (starting index)
            order_by: Field to order by (default: date_posted)
            order_direction: Order direction ("asc" or "desc", default: "desc")
            category: Optional category to filter by

        Returns:
            Dictionary containing jobs list and metadata
        """
        try:
            # Build the query
            query = self.db.collection('jobs')

            # Filter by category if provided
            if category:
                query = query.where('category', '==', category)

            # Add ordering
            if order_direction.lower() == "desc":
                query = query.order_by(order_by, direction=Query.DESCENDING)
            else:
                query = query.order_by(order_by, direction=Query.ASCENDING)

            # Apply offset and limit
            query = query.offset(offset).limit(limit)

            # Execute query
            docs = query.stream()

            jobs = []
            for doc in docs:
                data = doc.to_dict()
                data = self._deserialize_datetime(data)
                job_application = JobApplication(**data)
                jobs.append(job_application.model_dump())

            # Get total count for pagination metadata
            total_query = self.db.collection('jobs')
            if category:
                total_query = total_query.where('category', '==', category)
            total_docs = list(total_query.stream())
            total_count = len(total_docs)

            return {
                "jobs": jobs,
                "total_count": total_count,
                "current_page": (offset // limit) + 1 if limit > 0 else 1,
                "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
                "has_next": offset + limit < total_count,
                "has_previous": offset > 0,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            print(f"Error fetching paginated jobs: {e}")
            return {
                "jobs": [],
                "total_count": 0,
                "current_page": 1,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
                "limit": limit,
                "offset": offset,
                "error": str(e)
            }

    # Utility Methods
    async def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Try to read from a test collection
            test_ref = self.db.collection('_health_check').document('test')
            test_ref.set({'timestamp': datetime.now(timezone.utc)})

            # Try to read it back
            doc = test_ref.get()
            return doc.exists
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False

    # Queue Operations
    async def get_oldest_queue_item(self) -> Optional[dict]:
        """
        Get the oldest item from the queue collection.

        Returns:
            Dictionary with queue item data including document ID, or None if queue is empty
        """
        try:
            query = (
                self.db.collection('queue')
                .order_by('created_at', direction=Query.ASCENDING)
                .limit(1)
            )
            docs = list(query.stream())

            if docs:
                doc = docs[0]
                data = doc.to_dict()
                data['_doc_id'] = doc.id
                print(f"[Queue] Found oldest item: {doc.id}")
                return data
            return None
        except Exception as e:
            print(f"[Queue] Error getting oldest queue item: {e}")
            return None

    async def delete_queue_item(self, doc_id: str) -> bool:
        """
        Delete a queue item by document ID.

        Args:
            doc_id: The Firestore document ID to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.db.collection('queue').document(doc_id).delete()
            print(f"[Queue] Deleted queue item: {doc_id}")
            return True
        except Exception as e:
            print(f"[Queue] Error deleting queue item {doc_id}: {e}")
            return False

    async def update_queue_item_status(self, doc_id: str, status: str, error: Optional[str] = None) -> bool:
        """
        Update the status of a queue item.

        Args:
            doc_id: The Firestore document ID
            status: New status (e.g., 'processing', 'completed', 'failed')
            error: Optional error message if status is 'failed'

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now(timezone.utc)
            }
            if error:
                update_data['error'] = error

            self.db.collection('queue').document(doc_id).update(update_data)
            print(f"[Queue] Updated queue item {doc_id} status to: {status}")
            return True
        except Exception as e:
            print(f"[Queue] Error updating queue item {doc_id}: {e}")
            return False

    async def get_pending_queue_items_count(self) -> int:
        """
        Get the count of pending items in the queue.

        Returns:
            Number of pending queue items
        """
        try:
            query = self.db.collection('queue').where('status', '==', None)
            docs = list(query.stream())
            return len(docs)
        except Exception as e:
            print(f"[Queue] Error counting queue items: {e}")
            return 0

    async def get_user_data(self, applicant_id: str) -> Optional[dict]:
        """
        Get user data by applicant ID.

        Args:
            applicant_id: The user's ID

        Returns:
            Dictionary with user data, or None if not found
        """
        try:
            doc_ref = self.db.collection('users').document(applicant_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                print(f"[Queue] Found user data for: {applicant_id}")
                return data
            print(f"[Queue] No user data found for: {applicant_id}")
            return None
        except Exception as e:
            print(f"[Queue] Error getting user data: {e}")
            return None

db = DatabaseManager()
