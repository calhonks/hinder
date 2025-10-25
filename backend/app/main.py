import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from brightdata import bdclient
import logging
import json
from datetime import datetime



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

class HealthResponse(BaseModel):
    status: str
    brightdata_configured: bool

class DataInput(BaseModel):
    data: Dict[str, Any]
    filename: Optional[str] = None

class SaveDataResponse(BaseModel):
    status: str
    message: str
    file_path: str

class UploadPDFResponse(BaseModel):
    status: str
    message: str
    filename: str
    file_path: str

# Routes
@app.get("/")
def read_root():
    return {
        "message": "Hinder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/save-data", response_model=SaveDataResponse)
async def save_data(input_data: DataInput):
    """
    Args:
        input_data: DataInput object containing the data to save and optional filename
    Returns:
        SaveDataResponse with status, message, and file path
    """
    try:
        # Generate filename with timestamp if not provided
        if input_data.filename:
            filename = f"{input_data.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Save file in current working directory
        file_path = os.path.abspath(filename)
        
        # Write data to file
        with open(file_path, 'w', encoding='utf-8') as f:
            # Write data as formatted JSON
            json.dump(input_data.data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved successfully to {file_path}")
        
        return SaveDataResponse(
            status="success",
            message="Data saved successfully",
            file_path=file_path
        )
    
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

@app.post("/upload-pdf", response_model=UploadPDFResponse)
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
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = file.filename.replace(' ', '_')
        filename = f"{timestamp}_{original_filename}"
        
        # Full file path
        file_path = os.path.join(pdfs_dir, filename)
        
        # Read and save file content
        file_content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"PDF saved successfully to {file_path}")
        
        return UploadPDFResponse(
            status="success",
            message="PDF saved successfully",
            filename=filename,
            file_path=os.path.abspath(file_path)
        )
    
    except Exception as e:
        logger.error(f"Error saving PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving PDF: {str(e)}")