#Ingetst the transcript and resume for retrieval
import pdfplumber
from .utils import Chunk

def ingest_pdf(file_path: str) -> list[Chunk]:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            pages.append({"source": pdf.name, "page":i+1, "text":page.extract_text() or ""})
    return pages
