import os
from datetime import datetime, timezone
from typing import Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client
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

db = DatabaseManager()
