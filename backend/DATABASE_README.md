# JobFinder Backend - Database Setup

This backend service integrates with Google Firestore for data persistence and includes form field analysis capabilities.

## Setup Instructions

### 1. Firebase/Firestore Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or select existing one)
3. Enable Firestore Database:
   - Go to "Firestore Database" in the left sidebar
   - Click "Create database"
   - Choose "Start in test mode" for development
   - Select a location for your database

4. Create a service account:
   - Go to Project Settings → Service accounts
   - Click "Generate new private key"
   - Download the JSON file

### 2. Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your Firebase credentials:
   ```env
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----"
   FIREBASE_CLIENT_EMAIL=your-service-account@project.iam.gserviceaccount.com
   FIREBASE_CLIENT_ID=your-client-id
   ```

   **Alternative**: Set the path to your service account JSON file:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 4. Run the Application

```bash
# Development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the startup script
python -m uvicorn app.main:app --reload
```

## API Endpoints

### Database Operations

- `POST /db/users` - Create user profile
- `GET /db/users/{user_id}` - Get user profile
- `PUT /db/users/{user_id}` - Update user profile
- `DELETE /db/users/{user_id}` - Delete all user data (GDPR)
- `POST /db/applications` - Create job application
- `GET /db/users/{user_id}/applications` - Get user's applications
- `PUT /db/applications/{app_id}/status` - Update application status
- `POST /db/field-analyses` - Save field analysis
- `GET /db/field-analyses/{analysis_id}` - Get field analysis
- `GET /db/field-analyses/by-url?url=...` - Get analyses by URL
- `GET /db/health` - Database health check

### Form Field Analysis

- `POST /fields/analyze` - Analyze application form fields

## Data Models

### UserProfile
```python
{
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "linkedin_url": "https://linkedin.com/in/user",
    "portfolio_url": "https://portfolio.com",
    "resume_url": "https://storage.com/resume.pdf",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

### JobApplication
```python
{
    "application_id": "uuid",
    "user_id": "uuid",
    "job_url": "https://company.com/jobs/123",
    "company_name": "Example Corp",
    "position_title": "Software Developer",
    "application_date": "2024-01-01T00:00:00Z",
    "status": "applied",  # applied, pending, interview, rejected, accepted
    "field_analysis_id": "uuid",
    "notes": "Additional notes",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### FieldAnalysis
```python
{
    "analysis_id": "uuid",
    "url": "https://company.com/apply",
    "fields": [
        {
            "element_id": "name",
            "field_type": "name",
            "label": "Full Name",
            "name": "full_name",
            "placeholder": "Enter your name",
            "required": true,
            "selector": "#name",
            "bounding_box": {"x": 100, "y": 200, "width": 300, "height": 40}
        }
    ],
    "field_count": 5,
    "screenshot_url": "/screenshots/analysis_123.png",
    "field_summary": {"name": 1, "email": 1, "phone": 1},
    "analyzed_at": "2024-01-01T00:00:00Z",
    "user_id": "uuid"
}
```

## Usage Examples

### Create a User
```bash
curl -X POST "http://localhost:8000/db/users" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "john@example.com",
    "name": "John Doe",
    "phone": "+1234567890"
  }'
```

### Analyze Application Form
```bash
curl -X POST "http://localhost:8000/fields/analyze" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://jobs.example.com/apply",
    "user_id": "user-uuid",
    "save_to_db": true
  }'
```

### Create Job Application
```bash
curl -X POST "http://localhost:8000/db/applications" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_id": "user-uuid",
    "job_url": "https://jobs.example.com/software-developer",
    "company_name": "Example Corp",
    "position_title": "Software Developer",
    "field_analysis_id": "analysis-uuid"
  }'
```

## Security Notes

1. **Never commit `.env` files** - Add them to `.gitignore`
2. **Use different Firebase projects** for development/production
3. **Set up Firestore security rules** in production
4. **Regularly rotate service account keys**
5. **Use environment-specific configurations**

## Firestore Collections

The application creates these collections:
- `users` - User profiles
- `applications` - Job applications
- `field_analyses` - Form field analysis results
- `_health_check` - Health check documents

## Troubleshooting

### Common Issues

1. **"Missing Firebase credentials"**
   - Check that all required environment variables are set
   - Verify the service account JSON file path
   - Ensure the service account has Firestore permissions

2. **"Permission denied"**
   - Check Firestore security rules
   - Verify the service account has proper roles

3. **"Project not found"**
   - Verify `FIREBASE_PROJECT_ID` is correct
   - Ensure Firestore is enabled for the project

### Health Check
Visit `http://localhost:8000/db/health` to check database connectivity.

## Development Tips

1. Use Firebase Emulator Suite for local development
2. Set up different projects for dev/staging/production
3. Monitor Firestore usage in the Firebase console
4. Use Firestore indexes for complex queries
5. Implement proper error handling and logging
