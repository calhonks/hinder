# Hinder API Usage Guide

## Base URL
```
http://localhost:8000
```

## Available Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running and BrightData is configured.

**Response:**
```json
{
  "status": "healthy",
  "brightdata_configured": true
}
```

---

### 2. Scrape Single Profile
**POST** `/api/scrape/profile`

Scrape a single LinkedIn profile.

**Request Body:**
```json
{
  "url": "https://www.linkedin.com/in/username/"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    // LinkedIn profile data from BrightData
  },
  "error": null,
  "url": "https://www.linkedin.com/in/username/"
}
```

**Error Response:**
```json
{
  "status": "error",
  "data": null,
  "error": "Error message here",
  "url": "https://www.linkedin.com/in/username/"
}
```

---

### 3. Scrape Batch Profiles
**POST** `/api/scrape/batch`

Scrape multiple LinkedIn profiles (max 10 per request).

**Request Body:**
```json
{
  "urls": [
    "https://www.linkedin.com/in/user1/",
    "https://www.linkedin.com/in/user2/",
    "https://www.linkedin.com/in/user3/"
  ]
}
```

**Response:**
```json
{
  "status": "completed",
  "results": [
    {
      "status": "success",
      "data": { /* profile data */ },
      "error": null,
      "url": "https://www.linkedin.com/in/user1/"
    },
    {
      "status": "error",
      "data": null,
      "error": "Error message",
      "url": "https://www.linkedin.com/in/user2/"
    }
  ],
  "total": 3,
  "successful": 2,
  "failed": 1
}
```

---

### 4. Analyze Profile
**POST** `/api/analyze/profile`

Scrape and analyze a LinkedIn profile (with extensible analysis logic).

**Request Body:**
```json
{
  "url": "https://www.linkedin.com/in/username/"
}
```

**Response:**
```json
{
  "status": "success",
  "url": "https://www.linkedin.com/in/username/",
  "data": {
    "profile_data": { /* scraped data */ },
    "analysis": {
      "completeness_score": null,
      "keywords": [],
      "experience_years": null
    }
  }
}
```

---

## Frontend Integration Examples

### Using Fetch API

```javascript
// Scrape a single profile
async function scrapeProfile(linkedinUrl) {
  try {
    const response = await fetch('http://localhost:8000/api/scrape/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: linkedinUrl
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      console.log('Profile data:', data.data);
      return data.data;
    } else {
      console.error('Error:', data.error);
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

// Usage
scrapeProfile('https://www.linkedin.com/in/username/')
  .then(profileData => {
    // Handle profile data
  })
  .catch(error => {
    // Handle error
  });
```

### Using Axios

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Scrape multiple profiles
async function scrapeBatchProfiles(urls) {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/scrape/batch`, {
      urls: urls
    });
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error
      console.error('Server error:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('No response received');
    } else {
      console.error('Error:', error.message);
    }
    throw error;
  }
}

// Usage
scrapeBatchProfiles([
  'https://www.linkedin.com/in/user1/',
  'https://www.linkedin.com/in/user2/'
])
  .then(result => {
    console.log(`Scraped ${result.successful} profiles successfully`);
    console.log(`Failed: ${result.failed}`);
  });
```

### React Example

```jsx
import { useState } from 'react';

function ProfileScraper() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const [error, setError] = useState(null);

  const handleScrape = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/scrape/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setProfileData(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="LinkedIn profile URL"
      />
      <button onClick={handleScrape} disabled={loading}>
        {loading ? 'Scraping...' : 'Scrape Profile'}
      </button>
      
      {error && <div className="error">{error}</div>}
      {profileData && <div className="profile-data">{JSON.stringify(profileData)}</div>}
    </div>
  );
}
```

---

## Error Handling

The API uses standard HTTP status codes:

- **200**: Success
- **422**: Validation Error (invalid request body)
- **500**: Server Error
- **503**: Service Unavailable (BrightData not configured)

**Validation Errors:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "url"],
      "msg": "Must be a valid LinkedIn profile URL",
      "input": "https://invalid-url.com"
    }
  ]
}
```

---

## CORS Configuration

The API is configured to accept requests from all origins in development. Update the `allow_origins` in `main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Interactive API Documentation

Visit these URLs when the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can test endpoints directly from your browser.

