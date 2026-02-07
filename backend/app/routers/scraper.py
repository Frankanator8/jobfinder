import csv
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from jobspy import scrape_jobs
from ..schemas.job_app import JobApplication
from ..dbmanager import DatabaseManager

router = APIRouter(prefix="/scraper", tags=["scraper"])

# Rate limiting variables
_last_scrape_time = 0
_rate_limit_seconds = 5

def _parse_date_posted(date_value: Any) -> Optional[datetime]:
    """
    Safely parse date_posted from scraped data.

    Args:
        date_value: The date value from scraped data

    Returns:
        datetime object if successfully parsed, None otherwise
    """
    if date_value is None:
        return None

    try:
        # If it's already a datetime, return it
        if isinstance(date_value, datetime):
            return date_value

        # If it's a string, try to parse it
        if isinstance(date_value, str):
            # Remove any extra whitespace
            date_str = date_value.strip()
            if not date_str or date_str.lower() in ['none', 'null', '', 'n/a']:
                return None

            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

        # If we can't parse it, return None
        return None

    except Exception as e:
        print(f"Error parsing date '{date_value}': {e}")
        return None

def _jobs_are_different(existing_job: JobApplication, new_job: JobApplication) -> bool:
    """
    Compare two JobApplication objects to see if they have meaningful differences.

    Args:
        existing_job: The existing job in the database
        new_job: The newly scraped job

    Returns:
        True if jobs are different enough to warrant an update, False otherwise
    """
    # Compare key fields that might change
    key_fields = ['position_title', 'description', 'compensation', 'work_type', 'job_type', 'location']

    for field in key_fields:
        existing_value = getattr(existing_job, field, '')
        new_value = getattr(new_job, field, '')

        # Normalize values for comparison
        if existing_value != new_value:
            return True

    # Check if date_posted is significantly different (more than 1 day)
    if existing_job.date_posted and new_job.date_posted:
        time_diff = abs((existing_job.date_posted - new_job.date_posted).days)
        if time_diff > 1:
            return True

    return False

@router.get("/scrape-jobs")
async def scrape_jobs_endpoint(
    site_name: str = "indeed,linkedin,zip_recruiter,google",
    google_search_term: str = "software engineer jobs near NYC posted in the last 3 days",
    location: str = "New York, NY",
    results_wanted: int = 50,
    hours_old: int = 72,
    country_indeed: str = "USA",
    linkedin_fetch_description: bool = True
) -> Dict[str, Any]:
    """
    Scrape job listings from multiple job sites.
    Rate limited to once every 5 seconds.

    Args:
        site_name: Comma-separated list of sites to scrape from
        google_search_term: Search term for Google jobs
        location: Job location to search in
        results_wanted: Number of results to return
        hours_old: Maximum age of job postings in hours
        country_indeed: Country code for Indeed searches
        linkedin_fetch_description: Whether to fetch full descriptions from LinkedIn

    Returns:
        Dictionary containing scraped job data and metadata
    """
    global _last_scrape_time

    # Check rate limit
    current_time = time.time()
    if current_time - _last_scrape_time < _rate_limit_seconds:
        time_remaining = _rate_limit_seconds - (current_time - _last_scrape_time)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {time_remaining:.1f} more seconds before making another request."
        )

    try:
        # Update last scrape time
        _last_scrape_time = current_time

        # Parse site_name parameter into a list
        sites = [site.strip() for site in site_name.split(",")]

        # Scrape jobs
        jobs = scrape_jobs(
            site_name=sites,
            google_search_term=google_search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed,
            linkedin_fetch_description=linkedin_fetch_description
        )

        # Save to CSV
        jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)

        # Convert scraped jobs to JobApplication objects
        job_applications = []
        saved_count = 0
        updated_count = 0
        skipped_count = 0
        db_manager = DatabaseManager()

        for _, job_row in jobs.iterrows():
            try:
                # Parse date_posted safely
                parsed_date = _parse_date_posted(job_row.get('date_posted'))

                # Generate application_id - use scraped ID or create a UUID if not available
                scraped_id = job_row.get('id', '')
                application_id = str(scraped_id) if scraped_id else str(uuid.uuid4())

                # Create JobApplication object from scraped data
                job_application = JobApplication(
                    application_id=application_id,
                    job_url=str(job_row.get('job_url', '')),
                    company_name=str(job_row.get('company', 'Unknown')),
                    position_title=str(job_row.get('title', '')),
                    description=str(job_row.get('description', '')),
                    work_type=str(job_row.get('is_remote', '')),
                    location=str(job_row.get('location', None)) if job_row.get('location') else None,
                    job_type=str(job_row.get('job_type', '')),
                    date_posted=parsed_date,
                    compensation=str(str(job_row.get('min_amount', '')) + '-' + str(job_row.get('max_amount', '')) if job_row.get('min_amount') or job_row.get('max_amount') else 'Not specified'),
                    logo=str(job_row.get('company_logo', ''))
                )

                # Check if job already exists by URL or ID
                existing_job = None
                if job_application.job_url:
                    existing_job = await db_manager.get_job_by_url(job_application.job_url)

                if not existing_job and job_application.application_id:
                    existing_job = await db_manager.get_job_application(job_application.application_id)

                if existing_job:
                    # Job exists, check if it needs updating
                    if _jobs_are_different(existing_job, job_application):
                        # Update existing job
                        if await db_manager.update_job_application(existing_job.application_id, job_application):
                            updated_count += 1
                            job_applications.append(job_application.model_dump())
                            print(f"Updated job: {job_application.position_title} at {job_application.company_name}")
                    else:
                        # Job exists and hasn't changed significantly
                        skipped_count += 1
                        print(f"Skipped unchanged job: {job_application.position_title} at {job_application.company_name}")
                else:
                    # New job, save to Firebase
                    if await db_manager.create_job_application(job_application):
                        saved_count += 1
                        job_applications.append(job_application.model_dump())
                        print(f"Saved new job: {job_application.position_title} at {job_application.company_name}")

            except Exception as e:
                print(f"Error processing job: {e}")
                continue

        return {
            "success": True,
            "jobs_found": len(jobs),
            "jobs_saved_to_firebase": saved_count,
            "jobs_updated": updated_count,
            "jobs_skipped": skipped_count,
            "message": f"Successfully scraped {len(jobs)} jobs. Saved {saved_count} new jobs, updated {updated_count} existing jobs, skipped {skipped_count} unchanged jobs.",
            "csv_saved": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping jobs: {str(e)}"
        )

def _determine_work_type(description: str) -> str:
    """Determine work type from job description."""
    description_lower = description.lower()
    if 'remote' in description_lower:
        return 'remote'
    elif 'hybrid' in description_lower:
        return 'hybrid'
    elif 'on-site' in description_lower or 'onsite' in description_lower:
        return 'on-site'
    else:
        return 'not specified'

def _determine_job_type(description: str) -> str:
    """Determine job type from job description."""
    description_lower = description.lower()
    if 'part-time' in description_lower or 'part time' in description_lower:
        return 'part-time'
    elif 'contract' in description_lower or 'contractor' in description_lower:
        return 'contract'
    elif 'internship' in description_lower or 'intern' in description_lower:
        return 'internship'
    elif 'full-time' in description_lower or 'full time' in description_lower:
        return 'full-time'
    else:
        return 'full-time'  # Default to full-time

def scrape():
    """Legacy function - kept for backward compatibility"""
    pass
