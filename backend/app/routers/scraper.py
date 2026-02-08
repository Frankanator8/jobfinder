import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from jobspy import scrape_jobs
from ..schemas.job_app import JobApplication
from ..schemas.job_app import JobCategory
from ..dbmanager import DatabaseManager

router = APIRouter(prefix="/scraper", tags=["scraper"])

# Rate limiting variables
_last_scrape_time = 0
_rate_limit_seconds = 5

# ----- Predefined search terms per category -----
CATEGORY_SEARCH_TERMS: Dict[str, list] = {
    JobCategory.SOFTWARE_ENGINEERING.value: [
        "software engineer",
        "software developer",
        "backend engineer"
    ],
    JobCategory.DATA_SCIENCE.value: [
        "data scientist",
        "data analyst",
        "machine learning engineer"
    ],
    JobCategory.FINANCE.value: [
        "financial analyst",
        "accountant",
        "finance manager"
    ],
    JobCategory.MARKETING.value: [
        "marketing manager",
        "digital marketing specialist",
        "content marketer"
    ],
    JobCategory.DESIGN.value: [
        "UX designer",
        "graphic designer",
        "product designer"
    ],
    JobCategory.HEALTHCARE.value: [
        "registered nurse",
        "medical assistant",
        "healthcare administrator"
    ],
    JobCategory.SALES.value: [
        "sales representative",
        "account executive",
        "sales manager"
    ],
    JobCategory.OPERATIONS.value: [
        "operations manager",
        "logistics coordinator",
        "supply chain analyst"
    ],
    JobCategory.EDUCATION.value: [
        "teacher",
        "professor",
        "academic advisor"
    ],
    JobCategory.LEGAL.value: [
        "paralegal",
        "legal assistant",
        "lawyer"
    ],
    JobCategory.HUMAN_RESOURCES.value: [
        "HR manager",
        "recruiter",
        "talent acquisition specialist"
    ],
    JobCategory.CUSTOMER_SERVICE.value: [
        "customer service representative",
        "call center agent",
        "customer support specialist"
    ],
    JobCategory.OTHER.value: [
        "jobs hiring near me",
        "entry level jobs",
        "remote jobs"
    ],
}


@router.get("/categories")
async def get_categories() -> Dict[str, Any]:
    """Return the list of valid job categories with their predefined search terms."""
    return {
        "success": True,
        "categories": [
            {
                "value": c.value,
                "label": c.value.replace("_", " ").title(),
                "search_terms": CATEGORY_SEARCH_TERMS.get(c.value, []),
            }
            for c in JobCategory
        ],
    }


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

@router.get("/get-jobs")
async def get_jobs_endpoint(
    limit: int = 10,
    offset: int = 0,
    order_by: str = "date_posted",
    order_direction: str = "desc",
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch n jobs starting at a certain index from the Firestore database.

    Args:
        limit: Number of jobs to fetch (n) - default: 10
        offset: Number of jobs to skip (starting index i) - default: 0
        order_by: Field to order by - default: "date_posted"
        order_direction: Order direction ("asc" or "desc") - default: "desc"
        category: Optional JobCategory value to filter by (e.g. "software_engineering", "finance")

    Returns:
        Dictionary containing jobs list and pagination metadata
    """
    try:
        # Validate category if provided
        valid_categories = [c.value for c in JobCategory]
        if category and category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category '{category}'. Valid categories: {valid_categories}"
            )

        # Validate parameters
        if limit <= 0:
            raise HTTPException(
                status_code=400,
                detail="Limit must be greater than 0"
            )

        if offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Offset must be 0 or greater"
            )

        if order_direction.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400,
                detail="Order direction must be 'asc' or 'desc'"
            )

        # Create database manager instance
        db_manager = DatabaseManager()

        # Fetch jobs with pagination
        result = await db_manager.get_jobs_paginated(
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            category=category
        )

        # Check if there was an error in the database operation
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {result['error']}"
            )

        return {
            "success": True,
            "data": result,
            "message": f"Successfully fetched {len(result['jobs'])} jobs (offset: {offset}, limit: {limit})"
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching jobs: {str(e)}"
        )


@router.get("/scrape-jobs")
async def scrape_jobs_endpoint(
    site_name: str = "indeed,linkedin,zip_recruiter,google",
    location: str = "New York, NY",
    results_wanted: int = 50,
    hours_old: int = 72,
    country_indeed: str = "USA",
    linkedin_fetch_description: bool = True,
    category: str = "software_engineering"
) -> Dict[str, Any]:
    """
    Scrape job listings from multiple job sites using predefined search terms
    for the given category.
    Rate limited to once every 5 seconds.

    Args:
        site_name: Comma-separated list of sites to scrape from
        location: Job location to search in
        results_wanted: Number of results to return
        hours_old: Maximum age of job postings in hours
        country_indeed: Country code for Indeed searches
        linkedin_fetch_description: Whether to fetch full descriptions from LinkedIn
        category: Required JobCategory value (e.g. "software_engineering").

    Returns:
        Dictionary containing scraped job data and metadata
    """
    global _last_scrape_time

    # Validate category
    valid_categories = [c.value for c in JobCategory]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Valid categories: {valid_categories}"
        )
    resolved_category = category

    # Get the predefined search terms for this category
    search_terms = CATEGORY_SEARCH_TERMS.get(category, ["jobs"])

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

        db_manager = DatabaseManager()
        job_applications = []
        saved_count = 0
        updated_count = 0
        skipped_count = 0
        total_scraped = 0

        # Build a list of (term, site_subset) combos to cycle through.
        # This ensures we vary BOTH the search query and the platform,
        # maximising the chance of finding genuinely new listings.
        search_combos = []
        for term in search_terms:
            for site in sites:
                search_combos.append((term, [site]))

        # Maximum number of scrape attempts to avoid running forever.
        MAX_ATTEMPTS = len(search_combos) * 2
        attempts = 0

        # Cycle through (term, site) combos until we've saved enough NEW jobs
        combo_index = 0
        while saved_count < results_wanted and attempts < MAX_ATTEMPTS:
            current_term, current_sites = search_combos[combo_index % len(search_combos)]
            attempts += 1
            print(f"[Scraper] Attempt {attempts}: '{current_term}' on {current_sites} (need {results_wanted - saved_count} more new jobs)")

            try:
                jobs = scrape_jobs(
                    site_name=current_sites,
                    search_term=current_term,
                    google_search_term=current_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed=country_indeed,
                    linkedin_fetch_description=linkedin_fetch_description
                )
            except Exception as scrape_err:
                print(f"[Scraper] Error scraping '{current_term}' on {current_sites}: {scrape_err}")
                combo_index += 1
                continue

            total_scraped += len(jobs)
            new_in_this_batch = 0

            for _, job_row in jobs.iterrows():
                try:
                    parsed_date = _parse_date_posted(job_row.get('date_posted'))
                    scraped_id = job_row.get('id', '')
                    application_id = str(scraped_id) if scraped_id else str(uuid.uuid4())

                    # Capture the direct application URL if available
                    raw_direct = job_row.get('job_url_direct', None)
                    direct_url = str(raw_direct) if raw_direct and str(raw_direct).lower() not in ('', 'none', 'nan') else None

                    job_application = JobApplication(
                        application_id=application_id,
                        job_url=str(job_row.get('job_url', '')),
                        job_url_direct=direct_url,
                        company_name=str(job_row.get('company', 'Unknown')),
                        position_title=str(job_row.get('title', '')),
                        description=str(job_row.get('description', '')),
                        work_type=str(job_row.get('is_remote', '')),
                        location=str(job_row.get('location', None)) if job_row.get('location') else None,
                        job_type=str(job_row.get('job_type', '')),
                        date_posted=parsed_date,
                        compensation=str(str(job_row.get('min_amount', '')) + '-' + str(job_row.get('max_amount', '')) if job_row.get('min_amount') or job_row.get('max_amount') else 'Not specified'),
                        logo=str(job_row.get('company_logo', '')),
                        category=resolved_category,
                    )

                    # ── Validate required fields ──
                    _title = (job_application.position_title or '').strip()
                    _company = (job_application.company_name or '').strip()
                    _desc = (job_application.description or '').strip()

                    if not _title or _title.lower() in ('', 'none', 'nan'):
                        skipped_count += 1
                        continue
                    if not _company or _company.lower() in ('', 'none', 'nan', 'unknown'):
                        skipped_count += 1
                        continue
                    if not _desc or _desc.lower() in ('', 'none', 'nan') or len(_desc) < 20:
                        skipped_count += 1
                        continue

                    _comp = (job_application.compensation or '').strip()
                    if _comp in ('', 'nan-nan', 'None-None', '-', 'nan', 'None'):
                        job_application.compensation = 'Not specified'

                    # Check if job already exists by URL or ID
                    existing_job = None
                    if job_application.job_url:
                        existing_job = await db_manager.get_job_by_url(job_application.job_url)
                    if not existing_job and job_application.application_id:
                        existing_job = await db_manager.get_job_application(job_application.application_id)

                    if existing_job:
                        if _jobs_are_different(existing_job, job_application):
                            if await db_manager.update_job_application(existing_job.application_id, job_application):
                                updated_count += 1
                                job_applications.append(job_application.model_dump())
                                print(f"Updated job: {job_application.position_title} at {job_application.company_name}")
                        else:
                            skipped_count += 1
                            print(f"Skipped unchanged job: {job_application.position_title} at {job_application.company_name}")
                    else:
                        if await db_manager.create_job_application(job_application):
                            saved_count += 1
                            new_in_this_batch += 1
                            job_applications.append(job_application.model_dump())
                            print(f"Saved new job: {job_application.position_title} at {job_application.company_name}")

                except Exception as e:
                    print(f"Error processing job: {e}")
                    continue

            print(f"[Scraper] Batch done: {new_in_this_batch} new jobs from '{current_term}' on {current_sites} (total new: {saved_count}/{results_wanted})")

            # Move to next (term, site) combo for variety
            combo_index += 1

        if attempts >= MAX_ATTEMPTS and saved_count < results_wanted:
            print(f"[Scraper] Reached max attempts ({MAX_ATTEMPTS}). Saved {saved_count} new jobs out of {results_wanted} requested.")

        return {
            "success": True,
            "jobs_found": total_scraped,
            "jobs_saved_to_firebase": saved_count,
            "jobs_updated": updated_count,
            "jobs_skipped": skipped_count,
            "message": f"Scraped {total_scraped} jobs across {attempts} searches. Saved {saved_count} new jobs, updated {updated_count}, skipped {skipped_count} duplicates.",
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
