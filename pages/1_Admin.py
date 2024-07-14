#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
This subpage runs the admin web interface.
"""

import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
import os
import zipfile
import subprocess
import io
import json
import glob
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma

from modules.web_scraping_utils import scrape_commons_category, scrape_web_page_url
from modules.utils import load_files_and_embed
from config.config import *


def reset_conversation():
    """
    Reset the conversation: clear the chat history and clear the screen.
    """

    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.chat_history2 = ConversationBufferWindowMemory(k=MAX_MESSAGES_IN_MEMORY, return_messages=True)


def unzip_and_replace(file_path):
    # Check if the file is a zip file
    if zipfile.is_zipfile(file_path):
        # Create a ZipFile object
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Extract all the contents of the zip file in the same directory
            zip_ref.extractall(os.path.dirname(file_path))
        
        # Remove the original zip file
        os.remove(file_path)
        print(f"The file {file_path} has been unzipped and the original zip file has been removed.")
    else:
        print(f"The file {file_path} is not a zip file.")


def clear_memory_and_cache():
    st.cache_data.clear()
    st.cache_resource.clear()
    reset_conversation()


def restart_db():
    command = ['bash', './db.sh', 'restart']
    st.write("Wait 20 seconds...")
    try:
        subprocess.run(command, capture_output=True, text=True, timeout=20)
    except Exception:
        st.write("")


# Function to zip files. file_paths is a list of files.
def zip_files(file_paths):
    # Create an in-memory bytes buffer
    buffer = io.BytesIO()
    # Create a zip file in the buffer
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            with open(file_path, 'rb') as f:
                zipf.writestr(os.path.basename(file_path), f.read())
    # Seek to the beginning of the buffer
    buffer.seek(0)
    return buffer


def get_subcategories(category, depth=1, max_depth=9):
    if depth > max_depth:
        return []

    url = f"https://commons.wikimedia.org/wiki/Category:{category}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    categories = [category]
    subcat_div = soup.find('div', {'id': 'mw-subcategories'})
    if subcat_div:
        links = subcat_div.find_all('a')
        for link in links:
            if 'Category:' in link.get('title', ''):
                subcat = link.get('title').replace('Category:', '')
                categories.extend(get_subcategories(subcat, depth + 1, max_depth))

    return categories


def get_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')
    notfiltered_links = [link.get('href') for link in links if link.get('href')]
    filtered_links = [link for link in notfiltered_links if "en/item" in link]
    full_links = []
    for link in filtered_links:
        full_link = "https://www.europeana.eu" + link
        full_links.append(full_link)
    return full_links


st.set_page_config(page_title=ASSISTANT_NAME, page_icon=ASSISTANT_ICON)

if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL

if "temperature" not in st.session_state:
    st.session_state.temperature = DEFAULT_TEMPERATURE

if "password_ok" not in st.session_state:
    st.session_state.password_ok = False

if "input_password" not in st.session_state:
    st.session_state.input_password = ""

st.title("Admin")

st.sidebar.write(f"Model: {st.session_state.model} ({st.session_state.temperature})")

# Ask admin password to access admin menu
admin_password = os.getenv("ADMIN_PASSWORD", "YYYY")
input_password = st.sidebar.text_input("Enter admin password: ", type="password", value=st.session_state.input_password)
st.session_state.input_password = input_password
if st.session_state.input_password != admin_password:
    st.session_state.password_ok = False
else:
    st.session_state.password_ok = True

if st.session_state.password_ok:

    # # # # # # # # # # # # # # # # # # # # #
    # Side bar window: second page (Admin)  #
    # # # # # # # # # # # # # # # # # # # # #
    
    options = ['Upload PDF Files', 'Delete all PDF Files', 'Upload JSON Files (Web Pages)', 'Restore: Upload JSON Files (Web Pages) in ZIP Format', 'Backup: Upload JSON Files (Web Pages) in ZIP Format', 'Backup: Download all JSON Files (Web Pages) in ZIP Format', 'Delete all JSON Files (Web Pages)', 'List all Web Pages URLs', 'List all URLs from Europeana search pages', 'Scrape Web Pages', 'Scrape Web Pages from Wikimedia Commons', 'Embed Pages in DB', 'Model and Temperature', 'Clear Memory and Streamlit Cache', 'Upload File (not in the knowledge base)']
    choice = st.sidebar.radio("Make your choice: ", options)

    if choice == "Scrape Web Pages":
        st.caption("Give the web page URLs and the filter (CSS class). The pages will be scraped and saved in JSON files in the 'json_files' directory.")
        st.caption("""
                    Filter: 
                    - two-third last (balat / irpa)
                    - media-body (belgica / kbr)
                    - row mb-3 justify-content-center (europeana / kul, irpa, etc.)
                    """)
        filter = st.text_input("Filter: ")
        urls_box = st.text_area("URLs (one per line)", height=200)
        if st.button("Start"):
            if urls_box:
                urls = urls_box.splitlines()  # List of URLs
            for url in urls:
                if url and filter:
                    scrape_web_page_url(url, filter)
                    st.write(f"{url} web page scraped and saved in a JSON file!")

    elif choice == "Model and Temperature":
        st.caption("Change the model and the temperature for the present chat session.")
        model_list = [OPENAI_MENU, ANTHROPIC_MENU, GOOGLE_MENU, VERTEXAI_MENU, OLLAMA_MENU]
        st.session_state.model = st.selectbox('Model: ', model_list, DEFAULT_MENU_CHOICE)
        st.session_state.temperature = st.slider("Temperature: ", 0.0, 2.0, DEFAULT_TEMPERATURE)
        st.caption("OpenAI: 0-2, Anthropic: 0-1")

    elif choice == "Scrape Web Pages from Wikimedia Commons":
        st.caption("Give categories from Wikimedia Commons. The pages in the categories and subcategories will be scraped and saved in JSON files (one file per category or subcategory) in the 'json_files' directory (knowledge base).")
        categories_box = st.text_area("Categories (one per line)", height=200)
        if st.button("Start"):
            if categories_box:
                categories = categories_box.splitlines()  # List of categories
            for category in categories:
                if category:
                    st.write('Getting the list of subcategories...')
                    subcategories = get_subcategories(category)
                    for subcategory in subcategories:
                        st.write(f"Scraping the web pages... (Category: {subcategory})")
                        scrape_commons_category(subcategory)
                        st.write(f"Web pages scraped and saved in a JSON file!")

    elif choice == "Upload File (not in the knowledge base)":
        st.caption("Upload a file in the 'files' directory.")
        uploaded_file = st.file_uploader("Choose a file:")
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            file_name = uploaded_file.name
            with open(f"files/{file_name}", "wb") as file:
                file.write(bytes_data)
            st.success(f"File '{file_name}' uploaded and saved successfully!")
        else:
            st.warning("No file uploaded yet.")

    elif choice == "Upload PDF Files":
        st.caption("Upload PDF files in the 'pdf_files' directory (knowledge base).")
        uploaded_files = st.file_uploader("Choose PDF files:", type=["pdf"], accept_multiple_files=True)
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                file_name = uploaded_file.name
                with open(f"./files/pdf_files/{file_name}", "wb") as file:
                    file.write(bytes_data)
                st.success(f"File '{file_name}' uploaded and saved successfully!")
            else:
                st.warning("No file uploaded yet.")

    elif choice == 'List all Web Pages URLs':
        st.caption("List all the JSON files with their Web page URLs (knowledge base).")
        if st.button("Start"):
            json_files = glob.glob('files/json_files/*.json')
            for file in json_files:
                st.write(f"********* File: {file}")
                with open(file, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        st.write(f"URL: {item['url']}")

    elif choice == 'List all URLs from Europeana search pages':
        st.caption("List all URLs (Web pages) from Europeana search pages.")
        urls_box = st.text_area("URLs of Europeana search pages (one per line)", height=200)
        if st.button("Start"):
            if urls_box:
                urls = urls_box.splitlines()  # List of urls
            for url in urls:
                if url:
                    links = get_links(url)
                    for link in links:
                        st.write(link)

    elif choice == "Upload JSON Files (Web Pages)":
        st.caption("Upload JSON files (Web pages) in the 'json_files' directory (knowledge base). One or many JSON items (Web pages) per JSON file.")
        uploaded_files = st.file_uploader("Choose JSON files:", type=["json"], accept_multiple_files=True)
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                file_name = uploaded_file.name
                with open(f"./files/json_files/{file_name}", "wb") as file:
                    file.write(bytes_data)
                st.success(f"File '{file_name}' uploaded and saved successfully!")
            else:
                st.warning("No file uploaded yet.")

    elif choice == "Restore: Upload JSON Files (Web Pages) in ZIP Format":
        st.caption("Upload JSON files (Web pages) in the 'json_files' directory (knowledge base). One or many JSON items (Web pages) per JSON file. The ZIP files will be unziped.")
        uploaded_files = st.file_uploader("Choose ZIP files:", type=["zip"], accept_multiple_files=True)
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                file_name = uploaded_file.name
                with open(f"./files/json_files/{file_name}", "wb") as file:
                    file.write(bytes_data)
                unzip_and_replace(f"./files/json_files/{file_name}")
                st.success(f"File '{file_name}' uploaded and unziped successfully!")
            else:
                st.warning("No file uploaded yet.")

    elif choice == "Backup: Upload JSON Files (Web Pages) in ZIP Format":
        st.caption("Upload JSON files (Web pages) in the 'backup_files' directory. One or many JSON items (Web pages) per JSON file. The ZIP files will NOT be unziped.")
        uploaded_files = st.file_uploader("Choose ZIP files:", type=["zip"], accept_multiple_files=True)
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                file_name = uploaded_file.name
                with open(f"./files/backup_files/{file_name}", "wb") as file:
                    file.write(bytes_data)
                #unzip_and_replace(f"./files/json_files/{file_name}")
                st.success(f"File '{file_name}' uploaded successfully!")
            else:
                st.warning("No file uploaded yet.")

    elif choice == "Backup: Download all JSON Files (Web Pages) in ZIP Format":
        st.caption("Download all JSON files (Web pages) in ZIP format. One or many JSON items (Web pages) per JSON file.")
        JSON_FILES_DIR = "./files/json_files/"
        json_files = os.listdir(JSON_FILES_DIR)
        json_paths = []
        for json_file in json_files:
            json_path = f"{JSON_FILES_DIR}{json_file}"
            json_paths.append(json_path)
        zipped_file = zip_files(json_paths)
        st.download_button(
            label="Download all JSON Files (Web Pages) in ZIP Format",
            data=zipped_file,
            file_name="ai-assistant-all-json-files.zip",
            mime="application/zip"
        )

    elif choice == "Clear Memory and Streamlit Cache":
        st.caption("Clear the Langchain and Streamlit memory buffer and the Streamlit cache.")
        if st.button("Clear Memory and Streamlit Cache"):
            clear_memory_and_cache()
            st.write("Done!")

    elif choice == "Delete all PDF Files":
        st.caption("Delete all the PDF files in the 'pdf_files' directory (knowledge base).")
        if st.button("Delete all PDF Files"):
            command = ['rm', '-Rf', './files/pdf_files/']
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            except Exception as e:
                st.write(f"Error: {e}")
            st.write(result.stdout)
            st.write(result.stderr)
            command = ['mkdir', '-p', './files/pdf_files/']
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            except Exception as e:
                st.write(f"Error: {e}")
            st.write(result.stdout)
            st.write(result.stderr)
            st.write("Done!")

    elif choice == "Delete all JSON Files (Web Pages)":
        st.caption("Delete all the JSON files (Web pages) in the 'json_files' directory (knowledge base).")
        if st.button("Delete all JSON Files (Web Pages)"):
            command = ['rm', '-Rf', './files/json_files/']
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            except Exception as e:
                st.write(f"Error: {e}")
            st.write(result.stdout)
            st.write(result.stderr)
            command = ['mkdir', '-p', './files/json_files/']
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            except Exception as e:
                st.write(f"Error: {e}")
            st.write(result.stdout)
            st.write(result.stderr)
            st.write("Done!")

    elif choice == "Embed Pages in DB":
        # Embed data in Chroma DB
        # Load and index

        st.caption('Embed all the web and pdf pages (knowledge base) in the Chroma vector DB (knowledge base).')

        JSON_FILES_DIR = "./files/json_files/"
        PDF_FILES_DIR = "./files/pdf_files/"

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
            load_files_and_embed(json_paths, pdf_paths, embed=True)
            clear_memory_and_cache()
            st.write("Done!")

        if st.button("Delete DB"):
            chroma_server_password = os.getenv("CHROMA_SERVER_AUTHN_CREDENTIALS", "YYYY")
            chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT, settings=Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider", chroma_client_auth_credentials=chroma_server_password))
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            vector_db = Chroma(collection_name=CHROMA_COLLECTION_NAME, client=chroma_client)
            vector_db.reset_collection()
            clear_memory_and_cache()
            st.write("Done!")

        if st.button("Restart DB (locally only)"):
            restart_db()
            st.write("Done!")

        if st.button("Files and DB Info"):
            load_files_and_embed(json_paths, pdf_paths, embed=False)
            st.write(f"Location of the Chroma vector DB: {CHROMA_SERVER_HOST}:{CHROMA_SERVER_PORT}")
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            chroma_server_password = os.getenv("CHROMA_SERVER_AUTHN_CREDENTIALS", "YYYY")
            chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT, settings=Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider", chroma_client_auth_credentials=chroma_server_password))
            vector_db = Chroma(collection_name=CHROMA_COLLECTION_NAME, client=chroma_client)
            nbr_embeddings = len(vector_db.get()['documents'])
            st.write(f"Number of embeddings in the Chroma vector DB: {nbr_embeddings}")

            try:

                path = './'
                files = os.listdir(path)
                st.write("Root path (local filesystem):")
                st.write(files)

            except Exception as e:
                st.write(f"Error: {e}")
