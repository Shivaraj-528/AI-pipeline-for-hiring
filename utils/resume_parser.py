# utils/resume_parser.py

from pypdf import PdfReader
from docx import Document
import os
import re



def parse_pdf(file_path):
    text = ""
    reader = PdfReader(file_path)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "

    return text.strip()


def parse_docx(file_path):
    text = ""
    doc = Document(file_path)

    for para in doc.paragraphs:
        text += para.text + " "

    return text.strip()


def extract_resume_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Resume file not found")

    if file_path.endswith(".pdf"):
        return parse_pdf(file_path)

    elif file_path.endswith(".docx"):
        return parse_docx(file_path)

    else:
        raise ValueError("Unsupported file format. Use PDF or DOCX.")

def extract_email(resume_text):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
    if match:
        return match.group(0)
    return None
def extract_resume_data(resume_text):
    return {
        "email": extract_email(resume_text),
        "text": resume_text
    }

