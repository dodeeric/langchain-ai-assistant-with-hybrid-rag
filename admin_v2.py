#!/usr/bin/env python

"""
Web interface to:
1. crawl/scrape web pages
2. embed data
"""

# v1: Scrape Europeana
# v2: Embed in Chroma DB

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import requests, json, shutil
from bs4 import BeautifulSoup
from modules.scrape_web_page_v1 import scrape_web_page
import streamlit as st
import dotenv, os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

dotenv.load_dotenv()

def scrape_commons_category(category):
    """
    METHOD 3: For Commons: Scrape the URLs from a Commons Category and save the results in a JSON file
    """
    
    FILE_PATH = "./files/commons-"

    #category = "Category:Prince_Philippe,_Count_of_Flanders_in_photographs"

    items = []
    href_old = ""

    # Step 1: Load the HTML content from a webpage
    url = f"https://commons.wikimedia.org/wiki/{category}"
    response = requests.get(url)
    html_content = response.text

    # Step 2: Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Find all URLs in  tags
    urls = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            #print(href)
            if href.startswith("/wiki/File:") and href != href_old: # This test because all links are in double!
                urls.append(f"https://commons.wikimedia.org{href}")
                href_old = href

    number_of_pages = len(urls)
    print(f"Number of pages to scrape: {number_of_pages}")

    i = 1
    items = []
    for url in urls:
        print(f"{i}/{number_of_pages}")
        url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
        item = scrape_web_page(url, "hproduct commons-file-information-table")
        print(item)
        items.append(item)
        #time.sleep(1)
        i = i + 1

    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"{FILE_PATH}{category}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()
    
def scrape_europeana_url(url):
    """
    METHOD 4: Scrape one URL (should be Europeana) and save the result in a JSON file
    """

    #url = "https://www.europeana.eu/en/item/0940429/_nhtSx4z"

    # Step 1: Load the HTML content from a webpage
    #response = requests.get(url)
    #html_content = response.text

    # Step 2: Parse the HTML content
    #soup = BeautifulSoup(html_content, 'html.parser')

    url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
    item = scrape_web_page(url, "card metadata-box-card mb-3")
    print(item)
    items = []
    items.append(item)   # Add in a list, even if only one item

    url2 = url.replace("https://","")
    url2 = url2.replace("http://","")
    url2 = url2.replace("/","-")
    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"./files/{url2}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()

def load_files_and_embed(json_file_paths, pdf_file_paths):
    """
    Loads and chunks files into a list of documents then embed
    """

    EMBEDDING_MODEL = "text-embedding-3-large"
    COLLECTION_NAME = "bmae"

    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    nbr_files = len(json_file_paths)
    st.write(f">>> Embed {nbr_files} JSON files...")
    documents = []
    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()   # 1 JSON item per chunk
        print(f"JSON file: {json_file_path}, Number of JSON items: {len(docs)}")
        documents = documents + docs
    st.write(f"Total number of JSON items: {len(documents)}")
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    nbr_files = len(pdf_file_paths)
    st.write(f">>> Embed {nbr_files} PDF files...")
    documents = []
    if pdf_file_paths:  # if equals to "", then skip
        for pdf_file_path in pdf_file_paths:
            loader = PyPDFLoader(pdf_file_path)
            pages = loader.load_and_split()  # 1 pdf page per chunk
            print(f"PDF file: {pdf_file_path}, Number of PDF pages: {len(pages)}")
            documents = documents + pages
    st.write(f"Total number of PDF pages: {len(documents)}")
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

def delete_directory(dir_path):
    try:
        shutil.rmtree(dir_path)
        print(f"Directory '{dir_path}' and all its contents have been deleted successfully")
    except FileNotFoundError:
        print(f"Error: Directory '{dir_path}' does not exist")
    except PermissionError:
        print(f"Error: Permission denied to delete '{dir_path}'")
    except Exception as e:
        print(f"Error: {e}")

# Main program

st.title("BMAE Admin")
st.caption("💬 BMAE, a chatbot powered by Langchain and Streamlit")

options = ['Scrape Commons', 'Scrape Europeana', 'Embed in DB']
choice = st.sidebar.radio("Make your choice: ", options)
#st.write(f'You selected: {choice}')

if choice == "Scrape Europeana":
    st.write("Give the web page URL of an item from Europeana (https://www.europeana.eu/en/item/xxx). The page will be scraped and saved in a JSON file (fields: web page url, metadata including the image url, scraped text).")
    url = st.text_input("Europeana URL: ")
    if url:
        st.write(f"Scraping the web page...")
        scrape_europeana_url(url)
        st.write(f"Web page scraped and saved in a JSON file!")
elif choice == "Embed in DB":
    # Embed data in Chroma DB
    # Load and index

    JSON_FILES_DIR = "./files/"
    PDF_FILES_DIR = "./pdf_files/"

    # JSON files
    json_files = os.listdir(JSON_FILES_DIR)
    json_paths = []
    for json_file in json_files:
        json_path = f"{JSON_FILES_DIR}{json_file}"
        json_paths.append(json_path)

    # PDF files
    pdf_files = os.listdir(PDF_FILES_DIR)
    pdf_paths = []
    for pdf_file in pdf_files:
        pdf_path = f"{PDF_FILES_DIR}{pdf_file}"
        pdf_paths.append(pdf_path)

    if st.button("Start Embed"):
        load_files_and_embed(json_paths, pdf_paths)
        st.write("Done!")

    if st.button("Delete DB"):
        delete_directory("./chromadb")
