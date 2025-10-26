# BrightData LinkedIn Scraper API Reference

This document provides comprehensive documentation for the `brightdata.py` module, which provides LinkedIn profile scraping capabilities using the BrightData API.

## Table of Contents
- [Overview](#overview)
- [Configuration](#configuration)
- [LinkedInProfile Class](#linkedinprofile-class)
- [Helper Function](#helper-function)
- [Usage Examples](#usage-examples)

---

## Overview

The `brightdata.py` module provides a Python interface for scraping LinkedIn profiles using the BrightData API. It includes both asynchronous scraping methods and data extraction utilities.

**Key Features:**
- Asynchronous profile scraping
- Automatic polling until scrape completion
- Data extraction helpers for common profile fields
- URL validation
- Comprehensive error handling

---

## Configuration

**Required Environment Variables:**
```bash
# Set one of these in your .env file
BRIGHTDATA_API=your_api_token_here
# OR
BRIGHTDATA_API_KEY=your_api_token_here
```

The module will automatically load these credentials using `python-dotenv`.

---

## LinkedInProfile Class

The `LinkedInProfile` class is the main interface for scraping and processing LinkedIn profile data.

### Constructor

```python
LinkedInProfile(url: str)
```

**Parameters:**
- `url` (str): The LinkedIn profile URL to scrape

**Attributes:**
- `url`: The LinkedIn profile URL
- `snapshot_id`: BrightData snapshot ID (populated after initiating scrape)
- `result`: The scraped profile data or status (populated during/after scraping)

**Example:**
```python
profile = LinkedInProfile("https://www.linkedin.com/in/example/")
```

---

### Async Scraping Methods

#### `validate_url(url: str) -> bool`

Validates that the provided URL is a valid LinkedIn profile URL.

**Parameters:**
- `url` (str): URL to validate

**Returns:**
- `bool`: True if valid LinkedIn profile URL, False otherwise

**Example:**
```python
profile = LinkedInProfile("https://www.linkedin.com/in/example/")
is_valid = profile.validate_url(profile.url)  # Returns True
```

---

#### `async initiate_scrape() -> bool`

Initiates a LinkedIn profile scrape via BrightData API and stores the snapshot ID.

**Returns:**
- `bool`: True if scrape initiated successfully, False otherwise

**Side Effects:**
- Sets `self.snapshot_id` with the BrightData snapshot ID

**Example:**
```python
profile = LinkedInProfile("https://www.linkedin.com/in/example/")
success = await profile.initiate_scrape()
if success:
    print(f"Scrape initiated. Snapshot ID: {profile.snapshot_id}")
```

**Error Handling:**
- Returns False for invalid URLs
- Returns False for API errors
- Prints error details to console

---

#### `async check_snapshot_status() -> bool`

Checks the status of an ongoing scrape operation.

**Returns:**
- `bool`: True if status check succeeded, False otherwise

**Side Effects:**
- Updates `self.result` with status string ("running", "ready", "failed", etc.)

**Example:**
```python
success = await profile.check_snapshot_status()
if success:
    print(f"Current status: {profile.result}")
```

---

#### `async get_info_from_snapshot() -> bool`

Retrieves the completed scrape data from BrightData.

**Returns:**
- `bool`: True if data retrieved successfully, False otherwise

**Side Effects:**
- Sets `self.result` with the full profile data dictionary

**Example:**
```python
success = await profile.get_info_from_snapshot()
if success:
    print(f"Profile data: {profile.result}")
```

---

#### `async scrape_linkedin_profile(poll_interval: int = 5) -> Dict`

**Main method** that orchestrates the complete scraping process: initiates scrape, polls for completion, and retrieves data.

**Parameters:**
- `poll_interval` (int, optional): Seconds to wait between status checks. Default: 5

**Returns:**
- `Dict`: The complete LinkedIn profile data

**Raises:**
- `Exception`: If any step fails (initiation, status check, data retrieval)
- `Exception`: If scraping status becomes "failed"

**Example:**
```python
profile = LinkedInProfile("https://www.linkedin.com/in/example/")
try:
    data = await profile.scrape_linkedin_profile(poll_interval=3)
    print(f"Successfully scraped profile: {data['name']}")
except Exception as e:
    print(f"Scraping failed: {e}")
```

**Process Flow:**
1. Validates URL and initiates scrape
2. Polls status every `poll_interval` seconds
3. Continues polling until status is "ready" or "failed"
4. Retrieves and returns final data

---

### Data Extraction Methods

These methods extract specific fields from the scraped profile data. They should be called **after** `scrape_linkedin_profile()` has completed successfully.

#### `get_linkedin_id() -> str`

Returns the LinkedIn user ID.

**Returns:**
- `str`: LinkedIn ID or None

**Example:**
```python
linkedin_id = profile.get_linkedin_id()
# Returns: "john-doe-12345"
```

---

#### `get_linkedin_name() -> str`

Returns the user's full name.

**Returns:**
- `str`: Full name or None

**Behavior:**
- Tries `result['name']` first
- Falls back to concatenating `first_name` + `last_name`
- Returns None if neither available

**Example:**
```python
name = profile.get_linkedin_name()
# Returns: "John Doe"
```

---

#### `get_linkedin_location() -> Dict`

Returns the user's location information.

**Returns:**
- `Dict` with keys:
  - `city` (str | None): City name
  - `country` (str | None): Country code

**Example:**
```python
location = profile.get_linkedin_location()
# Returns: {'city': 'San Francisco', 'country': 'US'}
```

---

#### `get_linkedin_current_company() -> Dict`

Returns information about the user's current company/position.

**Returns:**
- `Dict` with keys:
  - `company` (str | None): Company name
  - `company_id` (str | None): LinkedIn company ID
  - `title` (str | None): Current job title

**Example:**
```python
current_job = profile.get_linkedin_current_company()
# Returns: {
#   'company': 'TechCorp',
#   'company_id': 'techcorp',
#   'title': 'Senior Software Engineer'
# }
```

---

#### `get_linkedin_all_experience() -> List[Dict]`

Returns all work experience entries from the profile.

**Returns:**
- `List[Dict]`: List of experience dictionaries with keys:
  - `company` (str | None): Company name
  - `title` (str | None): Job title
  - `start_date` (str | None): Start date
  - `end_date` (str | None): End date
  - `description` (str | None): Job description

**Behavior:**
- Handles both simple experience entries and nested positions within a company
- Returns empty list if no experience data

**Example:**
```python
experience = profile.get_linkedin_all_experience()
# Returns: [
#   {
#     'company': 'TechCorp',
#     'title': 'Senior Engineer',
#     'start_date': '2020-01',
#     'end_date': None,
#     'description': 'Lead backend development...'
#   },
#   {
#     'company': 'StartupCo',
#     'title': 'Software Engineer',
#     'start_date': '2018-06',
#     'end_date': '2019-12',
#     'description': 'Full-stack development...'
#   }
# ]
```

---

#### `get_linkedin_education() -> List[Dict]`

Returns all education entries from the profile.

**Returns:**
- `List[Dict]`: List of education dictionaries with keys:
  - `school` (str): School/university name
  - `degree` (str | None): Degree name
  - `field` (str | None): Field of study
  - `start_year` (int | None): Start year
  - `end_year` (int | None): End year

**Example:**
```python
education = profile.get_linkedin_education()
# Returns: [
#   {
#     'school': 'MIT',
#     'degree': 'Bachelor of Science',
#     'field': 'Computer Science',
#     'start_year': 2014,
#     'end_year': 2018
#   }
# ]
```

---

## Helper Function

### `async enrich_profile(linkedin_url: str) -> Dict[str, Any]`

Convenience adapter function that wraps the scraping process and returns a standardized result format.

**Parameters:**
- `linkedin_url` (str): LinkedIn profile URL to scrape

**Returns:**
- `Dict` with one of these formats:
  
  **Success:**
  ```python
  {
    "enriched": True,
    "data": { /* full profile data */ }
  }
  ```
  
  **Failure:**
  ```python
  {
    "enriched": False,
    "error": "error message here"
  }
  ```

**Example:**
```python
result = await enrich_profile("https://www.linkedin.com/in/example/")
if result["enriched"]:
    print(f"Success! Profile data: {result['data']}")
else:
    print(f"Failed: {result['error']}")
```

**Error Cases:**
- Returns `{"enriched": False, "error": "missing_token"}` if BrightData API key not configured
- Returns `{"enriched": False, "error": "..."}` for any scraping errors

---

## Usage Examples

### Basic Usage (Single Profile)

```python
import asyncio
from app.services.brightdata import LinkedInProfile

async def scrape_profile():
    url = "https://www.linkedin.com/in/example/"
    profile = LinkedInProfile(url)
    
    try:
        # Scrape the profile
        data = await profile.scrape_linkedin_profile()
        
        # Extract specific information
        name = profile.get_linkedin_name()
        location = profile.get_linkedin_location()
        current_job = profile.get_linkedin_current_company()
        experience = profile.get_linkedin_all_experience()
        education = profile.get_linkedin_education()
        
        print(f"Name: {name}")
        print(f"Location: {location['city']}, {location['country']}")
        print(f"Current Position: {current_job['title']} at {current_job['company']}")
        print(f"Total Experience Entries: {len(experience)}")
        print(f"Education: {len(education)} degrees")
        
        return data
    except Exception as e:
        print(f"Error scraping profile: {e}")
        return None

# Run the async function
asyncio.run(scrape_profile())
```

---

### Using the Convenience Function

```python
import asyncio
from app.services.brightdata import enrich_profile

async def enrich_user_profile():
    url = "https://www.linkedin.com/in/example/"
    result = await enrich_profile(url)
    
    if result["enriched"]:
        profile_data = result["data"]
        print(f"Profile enriched successfully!")
        print(f"Name: {profile_data.get('name', 'N/A')}")
        print(f"Headline: {profile_data.get('headline', 'N/A')}")
    else:
        print(f"Enrichment failed: {result['error']}")

asyncio.run(enrich_user_profile())
```

---

### Batch Processing Multiple Profiles

```python
import asyncio
from app.services.brightdata import LinkedInProfile

async def scrape_multiple_profiles(urls: list[str]):
    """Scrape multiple LinkedIn profiles concurrently."""
    tasks = []
    
    for url in urls:
        profile = LinkedInProfile(url)
        tasks.append(profile.scrape_linkedin_profile())
    
    # Run all scrapes concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = []
    failed = []
    
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            failed.append({"url": url, "error": str(result)})
        else:
            successful.append({"url": url, "data": result})
    
    return {
        "successful": successful,
        "failed": failed,
        "total": len(urls)
    }

# Usage
urls = [
    "https://www.linkedin.com/in/user1/",
    "https://www.linkedin.com/in/user2/",
    "https://www.linkedin.com/in/user3/"
]

results = asyncio.run(scrape_multiple_profiles(urls))
print(f"Scraped {len(results['successful'])} profiles successfully")
print(f"Failed: {len(results['failed'])}")
```

---

### FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.brightdata import enrich_profile

app = FastAPI()

class ProfileRequest(BaseModel):
    url: str

@app.post("/api/enrich-profile")
async def enrich_linkedin_profile(request: ProfileRequest):
    """Endpoint to enrich a LinkedIn profile."""
    result = await enrich_profile(request.url)
    
    if not result["enriched"]:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to enrich profile: {result['error']}"
        )
    
    return {
        "status": "success",
        "profile": result["data"]
    }
```

---

### Custom Polling Interval

```python
import asyncio
from app.services.brightdata import LinkedInProfile

async def quick_scrape():
    """Use faster polling for time-sensitive scraping."""
    profile = LinkedInProfile("https://www.linkedin.com/in/example/")
    
    # Poll every 2 seconds instead of default 5
    data = await profile.scrape_linkedin_profile(poll_interval=2)
    
    return data

asyncio.run(quick_scrape())
```

---

### Error Handling Example

```python
import asyncio
from app.services.brightdata import LinkedInProfile

async def robust_scrape(url: str):
    """Scrape with comprehensive error handling."""
    profile = LinkedInProfile(url)
    
    # Validate URL first
    if not profile.validate_url(url):
        return {"success": False, "error": "Invalid LinkedIn URL"}
    
    try:
        data = await profile.scrape_linkedin_profile()
        
        # Verify we got data
        if not data:
            return {"success": False, "error": "No data returned"}
        
        # Extract and validate key fields
        name = profile.get_linkedin_name()
        if not name:
            print("Warning: Profile has no name")
        
        return {
            "success": True,
            "data": data,
            "name": name,
            "experience_count": len(profile.get_linkedin_all_experience()),
            "education_count": len(profile.get_linkedin_education())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

# Usage
result = asyncio.run(robust_scrape("https://www.linkedin.com/in/example/"))
if result["success"]:
    print(f"Successfully scraped {result['name']}")
else:
    print(f"Error: {result['error']}")
```

---

## Testing

The module includes a `__main__` block for manual testing:

```bash
# Set test URL in environment
export TEST_LINKEDIN_URL="https://www.linkedin.com/in/your-test-profile/"

# Run the module directly
python -m app.services.brightdata
```

This will scrape the specified profile and print the JSON result.

---

## Notes & Best Practices

1. **Rate Limiting**: BrightData API has rate limits. Consider implementing delays between batch requests.

2. **Timeouts**: The scraping process can take 30-60 seconds. Ensure your application handles long-running requests appropriately.

3. **Error Handling**: Always wrap scraping calls in try-except blocks. Network issues, API limits, and invalid profiles can all cause failures.

4. **Data Validation**: Not all LinkedIn profiles have complete data. Always check for None values when extracting fields.

5. **Async Context**: All scraping methods are async. Make sure to use `await` and run them in an async context (e.g., `asyncio.run()` or within an async function).

6. **Snapshot IDs**: Snapshot IDs are stored for debugging. Log them if you need to investigate issues with BrightData support.

7. **Polling Interval**: The default 5-second poll interval is reasonable. Shorter intervals may hit rate limits; longer intervals increase total scraping time.

8. **Environment Variables**: Never commit your BrightData API key to version control. Always use environment variables or secure secret management.

---

## API Response Structure

The raw data returned by BrightData includes these common fields:

```python
{
    "id": "linkedin-user-id",
    "name": "Full Name",
    "first_name": "First",
    "last_name": "Last",
    "headline": "Job Title at Company",
    "city": "City Name",
    "country_code": "US",
    "current_company": {
        "name": "Company Name",
        "company_id": "company-id",
        "title": "Current Title"
    },
    "experience": [
        {
            "company": "Company Name",
            "title": "Job Title",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM" or None,
            "description": "Job description...",
            "positions": [...]  # For multiple positions at same company
        }
    ],
    "education": [
        {
            "title": "School Name",
            "degree": "Degree Name",
            "field": "Field of Study",
            "start_year": 2014,
            "end_year": 2018
        }
    ],
    # ... many more fields available
}
```

Refer to BrightData's LinkedIn dataset documentation for the complete field list.
