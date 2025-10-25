import os
from typing import Optional
import fitz  # PyMuPDF

def extract_text(path: str) -> str:
    try:
        text = []
        doc = fitz.open(path)
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception as e:
        print(f"Error extracting text from {path}: {e}")

if __name__ == "__main__":
    print(extract_text(path="./../../pdfs/Resume_(5).pdf"))