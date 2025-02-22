import streamlit as st
import requests
import os
import boto3
import urllib.parse
from dotenv import load_dotenv

st.title("Welcome to DocGPT API Frontend")
st.header("Choose a function to process your document")

BASE_API_URL = "https://backend-image-416252648166.us-central1.run.app/"
#BASE_API_URL = "http://127.0.0.1:8000/docs"
S3_BUCKET_NAME = "document-parsed-files-1"
S3_PDF_OBJECT = "PDF_Files"
AWS_REGION = "us-east-2"

load_dotenv(dotenv_path="env")

# AWS Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

dropdown = st.sidebar.selectbox("Select the API endpoint", [
    "PyMuPDF", "BeautifulSoup", "Extract LXML", "MS Docs","Pytesseract","APIFY"
])

if dropdown == "PyMuPDF":
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        file_name, file_extension = os.path.splitext(uploaded_file.name)
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BASE_API_URL}/extract-pdf/", files=files)

        if response.status_code == 200:
            folder_prefix = f"{S3_PDF_OBJECT}/{file_name}/"
            aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
            st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)
        else:
            st.error(" Failed to process the file. Please try again.")

elif dropdown == "BeautifulSoup":
    st.sidebar.write("Enter the URL of the PDF:")
    url = st.sidebar.text_input("Enter the webpage URL", key="beautifulsoup_url")

    if url:
        response = requests.post(f"{BASE_API_URL}/parse-html/", data={"url": url})
        
        if response.status_code == 200:
            file_name = os.path.splitext(os.path.basename(url))[0]
            folder_prefix = f"Webpages/{file_name}/"
            aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
            st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)
        else:
            st.error(" Failed to process the file. Please try again.")

elif dropdown == "Extract LXML":
    url = st.sidebar.text_input("Enter the URL", key="lxml_url")
    
    if url:
        response = requests.post(f"{BASE_API_URL}/extract-lxml/", data={"url": url})
        
        if response.status_code == 200:
            file_name = os.path.splitext(os.path.basename(url))[0]
            folder_prefix = f"Webpages/{file_name}/"
            aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
            st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)
        else:
            st.error(" Failed to process the file. Please try again.")

elif dropdown == "MS Docs":
    uploaded_file = st.sidebar.file_uploader("Upload a Document", type=["pdf", "docx"], key="msdocs_uploader")
    
    if uploaded_file is not None:
        file_name, file_extension = os.path.splitext(uploaded_file.name)
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BASE_API_URL}/process-doc-intelligence/", files=files)

        if response.status_code == 200:
            folder_prefix = f"{S3_PDF_OBJECT}/{file_name}/"
            aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
            st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)
        else:
            st.error("Failed to process the file. Please try again.")

elif dropdown == "PyTesseract":
    st.sidebar.write("Upload an Image (JPG, PNG, TIFF, PDF)")
    uploaded_file = st.sidebar.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file is not None:
        original_filename = uploaded_file.name
        file_name, file_extension = os.path.splitext(original_filename)

        files = {"file": (original_filename, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BASE_API_URL}/extract-text-pytesseract/", files=files)

        if response.status_code == 200:
            try:
                data = response.json()
                content = data.get("ocr_text", "No extracted text available.") if isinstance(data, dict) else response.text
                
                st.write("### Extracted OCR Text")
                preview_length = min(1000, len(content))
                st.text_area("OCR Result", content[:preview_length] + "...", height=300)
                
                folder_prefix = f"{S3_PDF_OBJECT}/{file_name}/"
                aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
                st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error while processing API response: {str(e)}")
        else:
            st.error(" Failed to process the file. Please try again.")

elif dropdown == "APIFY":
    st.sidebar.write("Enter the URL to scrape:")
    url = st.sidebar.text_input("Enter the webpage URL", key="apify_scraper_url")

    if url:
        response = requests.post(f"{BASE_API_URL}/apify-scrape/", json={"url": url})  

        if response.status_code == 200:
            try:
                dt = response.json()
                scrape_status = dt.get("message", "Scraping completed!") if isinstance(dt, dict) else str(dt)

                st.write("### Scrape Status")
                preview_length = min(1000, len(scrape_status))
                st.text_area("Scrape Log", scrape_status[:preview_length] + "...", height=150)

                st.success("Webpage successfully scraped and uploaded to S3!")

                
                file_name = os.path.splitext(os.path.basename(url))[0]
                folder_prefix = f"Webpages/{file_name}/"
                aws_console_url = f"https://us-east-2.console.aws.amazon.com/s3/buckets/{S3_BUCKET_NAME}?region=us-east-2&prefix={urllib.parse.quote(folder_prefix)}"
                st.markdown(f"[Click here to access the folder in S3]({aws_console_url})", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error while processing API response: {str(e)}")
        else:
            st.error(f"Failed to scrape the webpage. Server Response: {response.text}")



                