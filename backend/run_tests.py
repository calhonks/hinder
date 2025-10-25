#!/usr/bin/env python3
"""
Simple test runner for LinkedIn Profile Scraper
Run this script directly without pytest if preferred.
"""

import asyncio
import sys
from app.brightdatatest import LinkedInProfile


# Test URLs
TEST_URLS = [
    'https://www.linkedin.com/in/alex-woelkers/',
    'https://www.linkedin.com/in/aytung/',
    'https://www.linkedin.com/in/daniel-hong-ucsc/',
    'https://www.linkedin.com/in/jubeenpark/',
    'https://www.linkedin.com/in/jacob-wei/',
]


async def test_profile(url: str):
    """Test scraping a single profile and extracting all data"""
    print(f"\n{'─'*80}")
    print(f"Testing: {url}")
    print(f"{'─'*80}")
    
    profile = LinkedInProfile(url)
    
    try:
        # Scrape the profile
        print("⏳ Initiating scrape...")
        result = await profile.scrape_linkedin_profile(poll_interval=5)
        
        # Extract all data
        linkedin_id = profile.get_linkedin_id()
        name = profile.get_linkedin_name()
        location = profile.get_linkedin_location()
        current_company = profile.get_linkedin_current_company()
        experience = profile.get_linkedin_all_experience()
        education = profile.get_linkedin_education()
        
        # Display results
        print(f"\n✅ SUCCESS - Profile Data:")
        print(f"   • ID: {linkedin_id}")
        print(f"   • Name: {name}")
        print(f"   • Location: {location['city']}, {location['country']}")
        print(f"   • Current Role: {current_company['title']} at {current_company['company']}")
        print(f"   • Experience: {len(experience)} position(s)")
        
        if len(experience) > 0:
            print(f"   • Latest Position:")
            print(f"      - {experience[0]['title']} at {experience[0]['company']}")
            print(f"      - {experience[0]['start_date']} to {experience[0]['end_date'] or 'Present'}")
        
        print(f"   • Education: {len(education)} entry(ies)")
        if len(education) > 0:
            print(f"   • Latest Education:")
            print(f"      - {education[0]['school']}")
            print(f"      - {education[0]['degree']} in {education[0]['field']}")
        
        return {
            'url': url,
            'success': True,
            'data': {
                'id': linkedin_id,
                'name': name,
                'location': location,
                'current_company': current_company,
                'experience_count': len(experience),
                'education_count': len(education)
            }
        }
        
    except Exception as e:
        print(f"\n❌ FAILED - Error: {str(e)}")
        return {
            'url': url,
            'success': False,
            'error': str(e)
        }


async def run_all_tests():
    """Run tests on all profiles"""
    print("\n" + "="*80)
    print("LinkedIn Profile Scraper - Test Suite")
    print("="*80)
    print(f"Testing {len(TEST_URLS)} profiles...")
    
    results = []
    
    for i, url in enumerate(TEST_URLS, 1):
        print(f"\n[{i}/{len(TEST_URLS)}]")
        result = await test_profile(url)
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"\n✅ Successful: {len(successful)}/{len(TEST_URLS)}")
    for r in successful:
        print(f"   • {r['data']['name']} ({r['url']})")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(TEST_URLS)}")
        for r in failed:
            print(f"   • {r['url']}")
            print(f"     Error: {r['error']}")
    
    print("\n" + "="*80)
    print(f"Final Score: {len(successful)}/{len(TEST_URLS)} profiles scraped successfully")
    print("="*80 + "\n")
    
    return results


if __name__ == '__main__':
    print("\nStarting tests...")
    print("Note: Each profile may take 30-60 seconds to scrape.")
    print("This test will take approximately 3-5 minutes total.\n")
    
    try:
        results = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        successful = sum(1 for r in results if r['success'])
        if successful == len(TEST_URLS):
            print("🎉 All tests passed!")
            sys.exit(0)
        elif successful > 0:
            print(f"⚠️  Partial success: {successful}/{len(TEST_URLS)} passed")
            sys.exit(1)
        else:
            print("❌ All tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)

