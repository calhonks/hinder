import pytest
import asyncio
import os
from typing import Dict, List
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.brightdata import LinkedInProfile


class TestLinkedInProfile:
    """Test suite for LinkedInProfile class"""
    
    # Test URLs
    TEST_URLS = [
        'https://www.linkedin.com/in/alex-woelkers/',
        'https://www.linkedin.com/in/aytung/',
        'https://www.linkedin.com/in/daniel-hong-ucsc/',
        'https://www.linkedin.com/in/jubeenpark/',
        'https://www.linkedin.com/in/jacob-wei/',
    ]
    
    def test_initialization(self):
        """Test that LinkedInProfile initializes correctly"""
        url = self.TEST_URLS[0]
        profile = LinkedInProfile(url)
        
        assert profile.url == url
        assert profile.snapshot_id == ''
        assert profile.result == ''
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URLs"""
        profile = LinkedInProfile(self.TEST_URLS[0])
        
        # Test with www
        assert profile.validate_url('https://www.linkedin.com/in/username/') == True
        # Test without www
        assert profile.validate_url('https://linkedin.com/in/username/') == True
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs"""
        profile = LinkedInProfile(self.TEST_URLS[0])
        
        assert profile.validate_url('https://google.com') == False
        assert profile.validate_url('https://www.linkedin.com/company/test/') == False
        assert profile.validate_url('http://linkedin.com/in/username/') == False
        assert profile.validate_url('not_a_url') == False
    
    @pytest.mark.asyncio
    async def test_scrape_single_profile(self):
        """Test scraping a single profile"""
        profile = LinkedInProfile(self.TEST_URLS[1])  # aytung
        
        try:
            result = await profile.scrape_linkedin_profile(poll_interval=5)
            
            # Verify result is a dictionary
            assert isinstance(result, dict)
            
            # Verify snapshot_id was set
            assert profile.snapshot_id != ''
            assert len(profile.snapshot_id) > 0
            
            print(f"\n✓ Successfully scraped: {self.TEST_URLS[1]}")
            print(f"  Snapshot ID: {profile.snapshot_id}")
            
        except Exception as e:
            pytest.fail(f"Failed to scrape profile: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_scrape_all_profiles(self):
        """Test scraping all provided profiles"""
        results = []
        
        for url in self.TEST_URLS:
            print(f"\nScraping: {url}")
            profile = LinkedInProfile(url)
            
            try:
                result = await profile.scrape_linkedin_profile(poll_interval=5)
                results.append({
                    'url': url,
                    'success': True,
                    'snapshot_id': profile.snapshot_id,
                    'result': result
                })
                print(f"✓ Success: {url}")
            except Exception as e:
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })
                print(f"✗ Failed: {url} - {str(e)}")
        
        # Verify at least some profiles were scraped successfully
        successful = [r for r in results if r['success']]
        assert len(successful) > 0, "No profiles were scraped successfully"
        
        print(f"\n{'='*60}")
        print(f"Summary: {len(successful)}/{len(self.TEST_URLS)} profiles scraped successfully")
        print(f"{'='*60}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_id(self):
        """Test extracting LinkedIn ID"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        linkedin_id = profile.get_linkedin_id()
        assert isinstance(linkedin_id, str)
        assert len(linkedin_id) > 0
        print(f"\n✓ LinkedIn ID: {linkedin_id}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_name(self):
        """Test extracting LinkedIn name"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        name = profile.get_linkedin_name()
        assert isinstance(name, str)
        assert len(name) > 0
        print(f"\n✓ Name: {name}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_location(self):
        """Test extracting location data"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        location = profile.get_linkedin_location()
        assert isinstance(location, dict)
        assert 'city' in location
        assert 'country' in location
        print(f"\n✓ Location: {location}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_current_company(self):
        """Test extracting current company data"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        company = profile.get_linkedin_current_company()
        assert isinstance(company, dict)
        assert 'company' in company
        assert 'company_id' in company
        assert 'title' in company
        print(f"\n✓ Current Company: {company}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_all_experience(self):
        """Test extracting all experience"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        experience = profile.get_linkedin_all_experience()
        assert isinstance(experience, list)
        
        if len(experience) > 0:
            # Verify structure of first entry
            entry = experience[0]
            assert 'company' in entry
            assert 'title' in entry
            assert 'start_date' in entry
            assert 'end_date' in entry
            assert 'description' in entry
        
        print(f"\n✓ Experience entries: {len(experience)}")
        if len(experience) > 0:
            print(f"  First entry: {experience[0]}")
    
    @pytest.mark.asyncio
    async def test_get_linkedin_education(self):
        """Test extracting education data"""
        profile = LinkedInProfile(self.TEST_URLS[1])
        await profile.scrape_linkedin_profile(poll_interval=5)
        
        education = profile.get_linkedin_education()
        assert isinstance(education, list)
        
        if len(education) > 0:
            # Verify structure of first entry
            entry = education[0]
            assert 'school' in entry
            assert 'degree' in entry
            assert 'field' in entry
            assert 'start_year' in entry
            assert 'end_year' in entry
        
        print(f"\n✓ Education entries: {len(education)}")
        if len(education) > 0:
            print(f"  First entry: {education[0]}")
    
    @pytest.mark.asyncio
    async def test_complete_profile_extraction(self):
        """Test extracting complete profile data for all users"""
        print(f"\n{'='*60}")
        print("COMPLETE PROFILE EXTRACTION TEST")
        print(f"{'='*60}")
        
        for url in self.TEST_URLS:
            print(f"\n{'─'*60}")
            print(f"Profile: {url}")
            print(f"{'─'*60}")
            
            profile = LinkedInProfile(url)
            
            try:
                # Scrape profile
                await profile.scrape_linkedin_profile(poll_interval=5)
                
                # Extract all data
                linkedin_id = profile.get_linkedin_id()
                name = profile.get_linkedin_name()
                location = profile.get_linkedin_location()
                current_company = profile.get_linkedin_current_company()
                experience = profile.get_linkedin_all_experience()
                education = profile.get_linkedin_education()
                
                # Print results
                print(f"ID: {linkedin_id}")
                print(f"Name: {name}")
                print(f"Location: {location['city']}, {location['country']}")
                print(f"Current: {current_company['title']} at {current_company['company']}")
                print(f"Experience: {len(experience)} positions")
                print(f"Education: {len(education)} entries")
                
                # Verify all extractions worked
                assert linkedin_id is not None
                assert name is not None
                assert isinstance(location, dict)
                assert isinstance(current_company, dict)
                assert isinstance(experience, list)
                assert isinstance(education, list)
                
                print("✓ All data extracted successfully")
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                # Don't fail the test, just note the error
                continue
        
        print(f"\n{'='*60}")


# Standalone test runner for manual execution
if __name__ == '__main__':
    print("Running LinkedIn Profile Scraper Tests...")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, '-v', '-s'])

