import os
import json
import asyncio
from typing import Dict
from dotenv import load_dotenv
import httpx

load_dotenv()

brightdata_token = os.getenv('BRIGHTDATA_API')
assert type(brightdata_token) == str

### brightdata api functions ###

# trigger the scrape based on linkedin url, return the snapshot id
async def initiate_scrape(url: str) -> str:
    headers = {
        "Authorization": "Bearer " + brightdata_token,
        "Content-Type": "application/json",
    }

    data = json.dumps({
        "input": [{"url":url}],
    })

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1viktl72bvl7bjuj0&notify=false&include_errors=true",
            headers=headers,
            content=data
        )
        return response.json()['snapshot_id']

# snapshot status check
async def check_snapshot_status(snapshot_id: str) -> str:
    url = "https://api.brightdata.com/datasets/v3/progress/" + snapshot_id
    headers = {
        "Authorization": "Bearer " + brightdata_token,
    }
    params = {
        "format": "json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response_json = response.json()
        return response_json['status']

# once snapshot ready, get data
async def get_info_from_snapshot(snapshot_id: str) -> Dict:
    url = "https://api.brightdata.com/datasets/v3/snapshot/" + snapshot_id
    headers = {
        "Authorization": "Bearer " + brightdata_token,
    }
    params = {
        "format": "json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        return response.json()

# put the process together, get the linkedin profile data
async def scrape_linkedin_profile(url: str, poll_interval: int = 5) -> Dict:
    """
    Main async function to scrape a LinkedIn profile.
    Can be called from a backend server to spawn async processes.
    
    Args:
        url: LinkedIn profile URL
        poll_interval: Seconds to wait between status checks (default: 5)
    
    Returns:
        Dict containing the scraped profile data
    """
    # Step 1: Initiate the scrape and get snapshot_id
    snapshot_id = await initiate_scrape(url)
    print(f"Scrape initiated. Snapshot ID: {snapshot_id}")
    
    # Step 2: Poll until status is 'ready'
    status = await check_snapshot_status(snapshot_id)
    print(f"Current status: {status}")
    
    while status != 'ready':
        await asyncio.sleep(poll_interval)  # Wait before checking again
        status = await check_snapshot_status(snapshot_id)
        print(f"Current status: {status}")
        
        if status == 'failed':
            print(f"Error: Scraping failed for snapshot {snapshot_id}")
            raise Exception(f"Scraping failed for snapshot {snapshot_id}")

    # Step 3: Get the final data
    print("Status is ready! Fetching data...")
    result = await get_info_from_snapshot(snapshot_id)
    # under the assumption that result is always a single result
    return result[0]

### processing the linkedin profile data ###

# get linkedin id
def linkedin_id(data: Dict) -> str:
    return data['id']

# get linkedin name
def linkedin_name(data: Dict) -> str:
    return data['name']

# get linkedin location
def linkedin_location(data: Dict) -> Dict:
    return {'city': data['city'], 'country': data['country_code']}

# get current company
def linkedin_current_company(data: Dict) -> Dict:
    return {'company': data['company'], 'company_id': data['company_id'], 'title': data['title']}

# get 

if __name__ == '__main__':
    # Example usage
    result = asyncio.run(scrape_linkedin_profile('https://www.linkedin.com/in/daniel-hong-ucsc/'))
    print(json.dumps(result, indent=2))