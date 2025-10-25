import os
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from brightdata import bdclient
import logging
import json
from datetime import datetime
import hashlib

import fitz

from .brightdatatest import scrape_linkedin_profile


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hinder API",
    description="API for LinkedIn profile scraping and analysis",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DataInput(BaseModel):
    data: Dict[str, Any]
    filename: Optional[str] = None

class UploadPDFResponse(BaseModel):
    file_id: str
    file_name: str

class NewProfileInfo(BaseModel):
    linkedin_url: str
    resume_file_id: str
    resume_file_name: str
    topics: List[str]
    available_now: bool

class ProfileResponse(BaseModel):
    name: str

class LinkedInScrapeRequest(BaseModel):
    linkedin_url: str
    
class LinkedInScrapeResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Routes
@app.get("/")
def read_root():
    return {
        "message": "Hinder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# profile creation
@app.post("/create-profile")
async def create_profile(newprofile: NewProfileInfo):
    return newprofile

# LinkedIn profile scraping
@app.post("/scrape-linkedin", response_model=LinkedInScrapeResponse)
async def scrape_linkedin(request: LinkedInScrapeRequest):
    """
    Scrape a LinkedIn profile asynchronously.
    
    Args:
        request: LinkedInScrapeRequest containing the LinkedIn URL
    
    Returns:
        LinkedInScrapeResponse with scraped profile data
    """
    try:
        logger.info(f"Starting LinkedIn scrape for: {request.linkedin_url}")
        
        # Call the async scraping function
        profile_data = await scrape_linkedin_profile(request.linkedin_url)
        
        logger.info(f"Successfully scraped LinkedIn profile: {request.linkedin_url}")
        
        return LinkedInScrapeResponse(
            status="success",
            message="LinkedIn profile scraped successfully",
            data=profile_data
        )
    
    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error scraping LinkedIn profile: {str(e)}"
        )

# pdf upload & parse
@app.post("/files", response_model=UploadPDFResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Saves an uploaded PDF file to a local directory.
    
    Args:
        file: PDF file to upload
    
    Returns:
        UploadPDFResponse with status, message, filename, and file path
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Create pdfs directory if it doesn't exist
        pdfs_dir = os.path.join(os.getcwd(), "pdfs")
        os.makedirs(pdfs_dir, exist_ok=True)
        # Generate MD5 hash of file content
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Reset file pointer for later reading
        await file.seek(0)
        # Generate unique filename with timestamp
        filename = file.filename.replace(' ', '_')
        
        # Full file path
        file_path = os.path.join(pdfs_dir, filename)
        
        # Read and save file content
        file_content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Parse PDF file
        resume_text = ''
        doc = fitz.open(file_path)
        for page in doc:
            text = page.get_text()
            resume_text += text

        # TODO: get info from resume text
        
        logger.info(f"PDF saved successfully to {file_path}")
        
        return UploadPDFResponse(
            file_id=file_hash,
            file_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error saving PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving PDF: {str(e)}")