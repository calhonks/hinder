# LinkedIn Profile Scraper Tests

This directory contains comprehensive unit tests for the LinkedIn Profile Scraper (`brightdatatest.py`).

## Test Coverage

The test suite validates:
- ✅ Profile initialization
- ✅ URL validation (valid and invalid URLs)
- ✅ Profile scraping for all 5 test profiles
- ✅ LinkedIn ID extraction
- ✅ Name extraction
- ✅ Location data extraction
- ✅ Current company extraction
- ✅ Work experience extraction
- ✅ Education history extraction
- ✅ Complete profile data extraction workflow

## Test Profiles

The tests run against these LinkedIn profiles:
1. https://www.linkedin.com/in/alex-woelkers/
2. https://www.linkedin.com/in/aytung/
3. https://www.linkedin.com/in/daniel-hong-ucsc/
4. https://www.linkedin.com/in/jubeenpark/
5. https://www.linkedin.com/in/jacob-wei/

## Running Tests

### Method 1: Using pytest (Recommended)

```bash
cd /mnt/c/Users/ddani/Documents/hackathons/hinder/backend

# Install dependencies
pip install pytest pytest-asyncio

# Run all tests with verbose output
pytest tests/test_brightdatatest.py -v -s

# Run specific test
pytest tests/test_brightdatatest.py::TestLinkedInProfile::test_validate_url_valid -v

# Run only the complete profile extraction test
pytest tests/test_brightdatatest.py::TestLinkedInProfile::test_complete_profile_extraction -v -s
```

### Method 2: Using the standalone test runner

```bash
cd /mnt/c/Users/ddani/Documents/hackathons/hinder/backend

# Run the simple test script
python run_tests.py
```

The standalone runner is simpler and doesn't require pytest installation.

## Expected Output

Each test will:
1. Scrape the LinkedIn profile via BrightData API
2. Extract all relevant data fields
3. Display the results with ✅ for success or ❌ for failure
4. Provide a summary at the end

Example output:
```
────────────────────────────────────────────────────────────────────────────────
Testing: https://www.linkedin.com/in/aytung/
────────────────────────────────────────────────────────────────────────────────
⏳ Initiating scrape...
Scrape initiated. Snapshot ID: s_abc123
Current status: running
Current status: ready
Status is ready! Fetching data...

✅ SUCCESS - Profile Data:
   • ID: aytung
   • Name: Albert Tung
   • Location: San Francisco, US
   • Current Role: Software Engineer at Tech Corp
   • Experience: 5 position(s)
   • Education: 2 entry(ies)
```

## Test Duration

- Each profile takes approximately 30-60 seconds to scrape
- Full test suite (5 profiles) takes approximately 3-5 minutes
- Individual tests are faster (test URL validation, etc.)

## Environment Requirements

Make sure you have:
- `BRIGHTDATA_API` environment variable set in `.env` file
- All dependencies installed from `requirements.txt`

## Troubleshooting

### "Failed to initiate scrape"
- Check that `BRIGHTDATA_API` token is set correctly
- Verify the token has proper permissions
- Check BrightData API status

### "Failed to check snapshot status"
- Network connectivity issue
- BrightData API may be experiencing issues

### Rate Limiting
If you're hitting rate limits, increase the `poll_interval` parameter:
```python
await profile.scrape_linkedin_profile(poll_interval=10)
```

## CI/CD Integration

To run tests in CI/CD pipelines:

```bash
# GitHub Actions example
- name: Run LinkedIn Scraper Tests
  run: |
    pip install -r requirements.txt
    pytest tests/test_brightdatatest.py --tb=short
  env:
    BRIGHTDATA_API: ${{ secrets.BRIGHTDATA_API }}
```

## Adding New Test Profiles

To test additional profiles, add URLs to the `TEST_URLS` list in either:
- `tests/test_brightdatatest.py` (for pytest)
- `run_tests.py` (for standalone runner)

## Notes

- Tests are async and use `pytest-asyncio` for async test support
- All tests handle missing data gracefully (returns `None` for missing fields)
- Tests validate data structure but not specific values (as profile data changes)

