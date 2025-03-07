from fastapi import FastAPI, File, UploadFile
import pdfplumber
import pytesseract
from PIL import Image
import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv  

load_dotenv("env")

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "/opt/homebrew/bin/tesseract")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the OCR API!"}


S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "document-parsed-files-1")
S3_PDF_OBJECT = "PDF_Files"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

def extract_text_with_ocr(pdf_path, image_folder):
    """
    Extract text from a PDF using OCR and save extracted images.
    """

    md_content = []
    os.makedirs(image_folder, exist_ok=True)

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            print(f"Processing page {page_number} for OCR...")

            # Convert PDF page to image
            page_image = page.to_image(resolution=300).original

            # Extract text using Tesseract OCR
            ocr_text = pytesseract.image_to_string(page_image)

            # Save extracted image
            image_filename = f"page_{page_number}.png"
            image_path = os.path.join(image_folder, image_filename)
            page_image.save(image_path)

            # Upload extracted images to S3
            s3_image_path = f"{image_folder}/{image_filename}"
            s3_client.upload_file(image_path, S3_BUCKET_NAME, s3_image_path)

            md_content.append(f"## Page {page_number}\n\n```\n{ocr_text}\n```\n![Extracted Image](Images/{image_filename})\n")

    return "\n".join(md_content)

@app.post("/extract-text-pytesseract/")
async def extract_ocr(file: UploadFile = File(...)):
    """
    API endpoint to receive a PDF file, process it using OCR, and store results in S3.
    """

    load_dotenv()

    # ✅ Extract correct filename
    original_filename = file.filename
    pdf_name, file_extension = os.path.splitext(original_filename)

    # ✅ Create a folder in S3 with the correct filename
    pdf_s3_folder = f"{S3_PDF_OBJECT}/{pdf_name}/"
    temp_pdf_path = f"/tmp/{original_filename}"
    image_folder = f"/tmp/{pdf_name}_Images"

    os.makedirs(image_folder, exist_ok=True)

    # ✅ Save uploaded file locally
    with open(temp_pdf_path, "wb") as buffer:
        buffer.write(file.file.read())

    try:
        # ✅ Upload original file to its correct folder in S3
        s3_client.upload_file(temp_pdf_path, S3_BUCKET_NAME, f"{pdf_s3_folder}{original_filename}")
    except NoCredentialsError:
        return {"error": "AWS credentials not found. Please configure them properly."}

    # ✅ Extract OCR text
    ocr_text = extract_text_with_ocr(temp_pdf_path, image_folder)

    # ✅ Save extracted text as Markdown
    output_markdown_file = f"/tmp/{pdf_name}_Extracted_Content.md"
    with open(output_markdown_file, "w", encoding="utf-8") as md_file:
        md_file.write(ocr_text)

    # ✅ Upload markdown content to S3
    s3_markdown_path = f"{pdf_s3_folder}Extracted_Content.md"
    s3_client.upload_file(output_markdown_file, S3_BUCKET_NAME, s3_markdown_path)

    return {
        "message": "OCR processing completed and stored in S3!",
        "s3_pdf_path": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}{original_filename}",
        "s3_extracted_markdown": f"s3://{S3_BUCKET_NAME}/{s3_markdown_path}",
        "s3_extracted_images_folder": f"s3://{S3_BUCKET_NAME}/{pdf_s3_folder}Images/"
    }
