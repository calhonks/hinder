import os
import json
import asyncio
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from brightdata import bdclient

load_dotenv()

brightdata_token = os.getenv('BRIGHTDATA_API')
assert type(brightdata_token) == str

client = bdclient(api_token=brightdata_token)

async def initiate_scrape(url: str) -> Dict[str, str]:
    scrape_result = await client.scrape_linkedin.profiles(url=url)
    result_json = json.dumps(scrape_result)
    return result_json

if __name__ == '__main__':

    result = initiate_scrape('https://www.linkedin.com/in/daniel-hong-ucsc/')
    print(result)