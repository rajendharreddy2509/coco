import os
import fitz  # PyMuPDF
from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection

router = APIRouter()
PDF_PATH = "data/coconut-farming.pdf"

def extract_text_from_pdf():
    """Extract text from the PDF file."""
    if not os.path.exists(PDF_PATH):
        raise HTTPException(status_code=404, detail="🚨 PDF file not found!")

    doc = fitz.open(PDF_PATH)
    text = "\n".join([page.get_text("text") for page in doc])
    return text.strip()

def store_text_in_db(extracted_text, conn):
    """Store extracted PDF text into the database."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO pdf_text (content) VALUES (%s)", (extracted_text,))
        conn.commit()

@router.post("/extract-pdf")
def extract_and_store_pdf(conn=Depends(get_db_connection)):
    """Extract text from PDF and store it in the database."""
    extracted_text = extract_text_from_pdf()
    store_text_in_db(extracted_text, conn)
    return {"message": "✅ Telugu PDF text extracted and stored!"}
