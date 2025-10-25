import os
from typing import Optional


def extract_text(path: str) -> str:
    try:
        import fitz  # PyMuPDF
        text = []
        doc = fitz.open(path)
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception:
        pass
    # fallback to pdfminer.six
    try:
        from io import StringIO
        from pdfminer.high_level import extract_text as pm_extract
        return pm_extract(path)
    except Exception:
        return ""
