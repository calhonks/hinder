from hmac import new
import os
import json
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv
import httpx

load_dotenv()

brightdata_token = os.getenv('BRIGHTDATA_API') or os.getenv('BRIGHTDATA_API_KEY') or ''

class LinkedInProfile():
### brightdata api functions ###
    def __init__(self, url: str) -> None:
        self.url = url
        self.snapshot_id = ''
        self.result = ''

    def validate_url(self, url: str) -> bool:
        return url.startswith("https://www.linkedin.com/in") or url.startswith("https://linkedin.com/in") 

    # trigger the scrape based on linkedin url, return the snapshot id
    async def initiate_scrape(self) -> bool:
        headers = {
            "Authorization": "Bearer " + brightdata_token,
            "Content-Type": "application/json",
        }

        if not self.validate_url(self.url):
            print(f"Invalid URL: {self.url}")
            return False

        data = json.dumps({
            "input": [{"url":self.url}],
        })

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1viktl72bvl7bjuj0&notify=false&include_errors=true",
                    headers=headers,
                    content=data
                )
                response.raise_for_status()
                response_data = response.json()
                print(f"BrightData Response: {response_data}")
                self.snapshot_id = response_data['snapshot_id']
                return True
        except Exception as e:
            print(f"Error in initiate_scrape: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return False

    # snapshot status check
    async def check_snapshot_status(self) -> bool:
        url = "https://api.brightdata.com/datasets/v3/progress/" + self.snapshot_id
        headers = {
            "Authorization": "Bearer " + brightdata_token,
        }
        params = {
            "format": "json",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response_json = response.json()
                self.result = response_json['status']
                return True
        except:
            return False
    
    # once snapshot ready, get data
    async def get_info_from_snapshot(self) -> bool:
        url = "https://api.brightdata.com/datasets/v3/snapshot/" + self.snapshot_id
        headers = {
            "Authorization": "Bearer " + brightdata_token,
        }
        params = {
            "format": "json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                # under assumption that result is always a single result
                self.result = response.json()[0]
                return True
        except:
            return False

    # put the process together, get the linkedin profile data
    async def scrape_linkedin_profile(self, poll_interval: int = 5) -> Dict:
        """
        Main async function to scrape a LinkedIn profile.
        Can be called from a backend server to spawn async processes.
        
        Args:
            poll_interval: Seconds to wait between status checks (default: 5)
        
        Returns:
            Dict containing the scraped profile data
        """
        # Step 1: Initiate the scrape and get snapshot_id
        success = await self.initiate_scrape()
        if not success:
            raise Exception("Failed to initiate scrape")
        print(f"Scrape initiated. Snapshot ID: {self.snapshot_id}")
        
        # Step 2: Poll until status is 'ready'
        success = await self.check_snapshot_status()
        if not success:
            raise Exception("Failed to check snapshot status")
        print(f"Current status: {self.result}")
        
        while self.result != 'ready':
            await asyncio.sleep(poll_interval)  # Wait before checking again
            success = await self.check_snapshot_status()
            if not success:
                raise Exception("Failed to check snapshot status")
            print(f"Current status: {self.result}")
            
            if self.result == 'failed':
                print(f"Error: Scraping failed for snapshot {self.snapshot_id}")
                raise Exception(f"Scraping failed for snapshot {self.snapshot_id}")

        # Step 3: Get the final data
        print("Status is ready! Fetching data...")
        success = await self.get_info_from_snapshot()
        if not success:
            raise Exception("Failed to get snapshot data")
        # under the assumption that result is always a single result
        return self.result

    ### processing the linkedin profile data ###

    # get linkedin id
    def get_linkedin_id(self) -> str:
        return self.result['id'] if self.result['id'] is not None else None

    # get linkedin name 
    def get_linkedin_name(self) -> str:
        if 'name' in self.result:
            return self.result['name'] if self.result['name'] is not None else None
        elif 'first_name' in self.result and 'last_name' in self.result:
            return self.result['first_name'] + ' ' + self.result['last_name'] if self.result['first_name'] is not None and self.result['last_name'] is not None else None
        else:
            return None

    # get linkedin location
    def get_linkedin_location(self) -> Dict:
        return {'city': self.result['city'] if self.result['city'] is not None else None,
                'country': self.result['country_code'] if self.result['country_code'] is not None else None}

    # get current company
    def get_linkedin_current_company(self) -> Dict:
        curr_company = ''
        if 'current_company' in self.result:
            curr_company = self.result['current_company']
        else:
            return {'company': None,
                    'company_id': None,
                    'title': 'None'}

        if self.result['current_company'] is not None:
            return {'company': self.result['current_company']['name'] if self.result['current_company']['name'] is not None else None,
                    'company_id': self.result['current_company']['company_id'] if self.result['current_company']['company_id'] is not None else None,
                    'title': self.result['current_company']['title'] if self.result['current_company']['title'] is not None else None}

    # get all experience
    def get_linkedin_all_experience(self) -> List[Dict]:
        out = []
        if self.result['experience'] is not None:
            for e in self.result['experience']:
                if 'positions' in e:
                    for p in e['positions']:
                        new_entry = {}
                        new_entry['company'] = e['company'] if 'company' in e else None
                        new_entry['title'] = p['title'] if 'title' in p else None
                        new_entry['start_date'] = p['start_date'] if 'start_date' in p else None
                        new_entry['end_date'] = p['end_date'] if 'end_date' in p else None
                        new_entry['description'] = p['description'] if 'description' in p else None
                        out.append(new_entry)
                else:
                    new_entry = {}
                    new_entry['company'] = e['company'] if 'company' in e else None
                    new_entry['title'] = e['title'] if 'title' in e else None
                    new_entry['start_date'] = e['start_date'] if 'start_date' in e else None
                    new_entry['end_date'] = e['end_date'] if 'end_date' in e else None
                    new_entry['description'] = e['description'] if 'description' in e else None
                    out.append(new_entry)
        return out

    # get education
    def get_linkedin_education(self) -> List[Dict]:
        out = []
        if self.result['education'] is not None:
            for e in self.result['education']:
                out.append({
                    'school': e['title'],
                    'degree': e['degree'] if 'degree' in e else None,
                    'field': e['field'] if 'field' in e else None,
                    'start_year': e['start_year'] if 'start_year' in e else None,
                    'end_year': e['end_year'] if 'end_year' in e else None
                })
        return out
    
# Adapter to match router expectation
async def enrich_profile(linkedin_url: str) -> Dict[str, Any]:
    """Runs the Bright Data scrape and returns a normalized result.
    Returns { enriched: bool, data?: dict, error?: str }
    """
    token = os.getenv('BRIGHTDATA_API') or os.getenv('BRIGHTDATA_API_KEY') or ''
    if not token:
        return {"enriched": False, "error": "missing_token"}
    try:
        profile = LinkedInProfile(linkedin_url)
        data = await profile.scrape_linkedin_profile()
        return {"enriched": True, "data": data}
    except Exception as e:
        return {"enriched": False, "error": str(e)}

if __name__ == '__main__':
    # Example usage for manual testing only
    test_url = os.getenv('TEST_LINKEDIN_URL', 'https://www.linkedin.com/in/example/')
    p = LinkedInProfile(test_url)
    result = asyncio.run(p.scrape_linkedin_profile())
    print(json.dumps(result, indent=2))