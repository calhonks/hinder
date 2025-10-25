# BrightData LinkedIn Scraper API Reference

## Overview

The `LinkedInProfile` class (located in `app/services/brightdata.py`) provides a Python interface for scraping LinkedIn profile data using the BrightData API. It handles the entire scraping lifecycle: initiating scrapes, polling for completion, and extracting structured profile information.

## Prerequisites

- BrightData API token set as `BRIGHTDATA_API` environment variable
- Python packages: `httpx`, `python-dotenv`

## Class: LinkedInProfile

### Constructor

```python
LinkedInProfile(url: str)
```

**Parameters:**
- `url` (str): LinkedIn profile URL (e.g., `https://www.linkedin.com/in/username/`)

**Returns:** LinkedInProfile instance

**Example:**
```python
profile = LinkedInProfile('https://www.linkedin.com/in/john-doe/')
```

---

## Core Methods

### scrape_linkedin_profile()

Main async method to scrape a LinkedIn profile. Orchestrates the entire scraping process.

```python
async def scrape_linkedin_profile(poll_interval: int = 5) -> Dict
```

**Parameters:**
- `poll_interval` (int, optional): Seconds to wait between status checks. Default: 5

**Returns:** Dict containing complete scraped profile data

**Raises:**
- `Exception`: If scraping fails at any stage

**Example:**
```python
import asyncio

profile = LinkedInProfile('https://www.linkedin.com/in/john-doe/')
result = await profile.scrape_linkedin_profile(poll_interval=3)
# or in sync context:
result = asyncio.run(profile.scrape_linkedin_profile())
```

---

### validate_url()

Validates if the provided URL is a valid LinkedIn profile URL.

```python
def validate_url(url: str) -> bool
```

**Parameters:**
- `url` (str): URL to validate

**Returns:** `True` if valid LinkedIn profile URL, `False` otherwise

**Example:**
```python
profile = LinkedInProfile('https://www.linkedin.com/in/john-doe/')
is_valid = profile.validate_url(profile.url)  # Returns True
```

---

### initiate_scrape()

Triggers a scrape job on BrightData and retrieves the snapshot ID.

```python
async def initiate_scrape() -> bool
```

**Returns:** `True` if scrape initiated successfully, `False` otherwise

**Side Effects:** Sets `self.snapshot_id` with the BrightData snapshot identifier

**Example:**
```python
success = await profile.initiate_scrape()
if success:
    print(f"Snapshot ID: {profile.snapshot_id}")
```

---

### check_snapshot_status()

Checks the current status of the scraping job.

```python
async def check_snapshot_status() -> bool
```

**Returns:** `True` if status check successful, `False` otherwise

**Side Effects:** Updates `self.result` with current status ('running', 'ready', or 'failed')

**Example:**
```python
success = await profile.check_snapshot_status()
if success:
    print(f"Status: {profile.result}")
```

---

### get_info_from_snapshot()

Retrieves the final scraped data once the snapshot is ready.

```python
async def get_info_from_snapshot() -> bool
```

**Returns:** `True` if data retrieved successfully, `False` otherwise

**Side Effects:** Populates `self.result` with complete profile data dictionary

**Example:**
```python
success = await profile.get_info_from_snapshot()
if success:
    print(f"Profile data: {profile.result}")
```

---

## Data Extraction Methods

These methods should be called after `scrape_linkedin_profile()` has completed successfully.

### get_linkedin_id()

Retrieves the LinkedIn profile ID.

```python
def get_linkedin_id() -> str
```

**Returns:** LinkedIn profile ID (string)

**Example:**
```python
profile_id = profile.get_linkedin_id()
# Returns: "john-doe-12345"
```

---

### get_linkedin_name()

Retrieves the full name from the profile.

```python
def get_linkedin_name() -> str
```

**Returns:** Full name (string)

**Example:**
```python
name = profile.get_linkedin_name()
# Returns: "John Doe"
```

---

### get_linkedin_location()

Retrieves the location information.

```python
def get_linkedin_location() -> Dict
```

**Returns:** Dictionary with location data:
```python
{
    'city': str,
    'country': str  # Country code
}
```

**Example:**
```python
location = profile.get_linkedin_location()
# Returns: {'city': 'San Francisco', 'country': 'US'}
```

---

### get_linkedin_current_company()

Retrieves current employment information.

```python
def get_linkedin_current_company() -> Dict
```

**Returns:** Dictionary with current company data:
```python
{
    'company': str | None,
    'company_id': str | None,
    'title': str | None
}
```

**Example:**
```python
current_job = profile.get_linkedin_current_company()
# Returns: {
#     'company': 'Tech Corp',
#     'company_id': 'tech-corp-123',
#     'title': 'Software Engineer'
# }
```

---

### get_linkedin_all_experience()

Retrieves complete work experience history.

```python
def get_linkedin_all_experience() -> List[Dict]
```

**Returns:** List of dictionaries, each containing:
```python
{
    'company': str | None,
    'title': str | None,
    'start_date': str | None,
    'end_date': str | None,
    'description': str | None
}
```

**Note:** Handles both single positions and multiple positions at the same company.

**Example:**
```python
experience = profile.get_linkedin_all_experience()
# Returns: [
#     {
#         'company': 'Tech Corp',
#         'title': 'Senior Engineer',
#         'start_date': '2020-01',
#         'end_date': None,
#         'description': 'Led development of...'
#     },
#     {
#         'company': 'Startup Inc',
#         'title': 'Junior Developer',
#         'start_date': '2018-06',
#         'end_date': '2020-01',
#         'description': 'Built features for...'
#     }
# ]
```

---

### get_linkedin_education()

Retrieves educational background.

```python
def get_linkedin_education() -> List[Dict]
```

**Returns:** List of dictionaries, each containing:
```python
{
    'school': str,
    'degree': str | None,
    'field': str | None,
    'start_year': str | None,
    'end_year': str | None
}
```

**Example:**
```python
education = profile.get_linkedin_education()
# Returns: [
#     {
#         'school': 'Stanford University',
#         'degree': 'Bachelor of Science',
#         'field': 'Computer Science',
#         'start_year': '2014',
#         'end_year': '2018'
#     }
# ]
```

---

## Complete Usage Example

```python
import asyncio
from app.services.brightdata import LinkedInProfile

async def main():
    # Initialize with LinkedIn URL
    profile = LinkedInProfile('https://www.linkedin.com/in/john-doe/')
    
    # Scrape the profile (this may take 30-60 seconds)
    try:
        result = await profile.scrape_linkedin_profile(poll_interval=5)
        print("Scraping completed successfully!")
        
        # Extract specific data
        name = profile.get_linkedin_name()
        location = profile.get_linkedin_location()
        current_job = profile.get_linkedin_current_company()
        experience = profile.get_linkedin_all_experience()
        education = profile.get_linkedin_education()
        
        # Use the data
        print(f"Name: {name}")
        print(f"Location: {location['city']}, {location['country']}")
        print(f"Current Role: {current_job['title']} at {current_job['company']}")
        print(f"Total Experience Entries: {len(experience)}")
        print(f"Education History: {len(education)} entries")
        
    except Exception as e:
        print(f"Error: {e}")

# Run the async function
asyncio.run(main())
```

---

## Error Handling

All async methods return boolean success indicators. The `scrape_linkedin_profile()` method raises exceptions on failure:

```python
try:
    result = await profile.scrape_linkedin_profile()
except Exception as e:
    if "Failed to initiate scrape" in str(e):
        # Handle scrape initiation failure (check API token, URL validity)
        pass
    elif "Failed to check snapshot status" in str(e):
        # Handle status check failure (network issues, API errors)
        pass
    elif "Failed to get snapshot data" in str(e):
        # Handle data retrieval failure
        pass
    elif "Scraping failed for snapshot" in str(e):
        # BrightData reported scraping failure
        pass
```

---

## Environment Variables

Required environment variable in `.env` file:

```bash
BRIGHTDATA_API=your_brightdata_api_token_here
```

---

## Notes

1. **Async Operations**: Most core methods are asynchronous and must be called with `await` or using `asyncio.run()`
2. **Rate Limits**: BrightData API has rate limits; handle appropriately in production
3. **Polling**: The default 5-second poll interval balances responsiveness and API usage
4. **Data Availability**: Not all fields may be present for every profile; methods handle missing data gracefully with `None` values
5. **Multiple Positions**: The experience extractor handles profiles where users held multiple positions at the same company

---

## Dependencies

```txt
httpx
python-dotenv
```

Install with:
```bash
pip install httpx python-dotenv
```

