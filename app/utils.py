import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from langchain_text_splitters import RecursiveCharacterTextSplitter
import io

# Setup text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF, falling back to OCR if a page is entirely an image."""
    doc = fitz.open(pdf_path)
    full_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # If very little text is found, it might be a scanned image
        if len(text.strip()) < 50:
            try:
                # Extract image for OCR
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                ocr_text = pytesseract.image_to_string(img)
                full_text.append(ocr_text)
            except Exception as e:
                print(f"OCR failed on page {page_num}: {e}")
                full_text.append(text)
        else:
            full_text.append(text)
            
    return "\n".join(full_text)

def chunk_text(text: str, metadata: dict) -> list:
    """Chunks text into smaller pieces while preserving metadata."""
    chunks = text_splitter.split_text(text)
    # Returning dicts that can be quickly processed later
    return [{"page_content": chunk, "metadata": metadata} for chunk in chunks]
