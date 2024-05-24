#!/usr/bin/env python

"""
This function runs the frontend web interface.
"""

# v2: stream output
# v3: integrate admin in main web interface
# v4: move model selection to admin interface + move files dir to json_files + add admin password
# v5: add a slider for the temperature + errors catch + use config.py

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from PIL import Image
from langchain.memory import ConversationBufferWindowMemory
import requests, json, shutil
from bs4 import BeautifulSoup
import streamlit as st
import os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from modules.scrape_web_page_v2 import scrape_web_page
from modules.assistant_backend_v2 import instanciate_ai_assistant_chain
from config.config import *

def scrape_commons_category(category):
    """
    METHOD 3: For Commons: Scrape the URLs from a Commons Category and save the results in a JSON file
    """
    
    FILE_PATH = "./json_files/commons-"

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
            if href.startswith("/wiki/File:") and href != href_old: # This test because all links are in double!
                urls.append(f"https://commons.wikimedia.org{href}")
                href_old = href

    number_of_pages = len(urls)
    st.write(f"Number of pages to scrape: {number_of_pages}")

    i = 1
    items = []
    for url in urls:
        st.write(f"Scraping {i}/{number_of_pages}...")
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
    with open(f"./json_files/{url2}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()


def load_files_and_embed(json_file_paths, pdf_file_paths):
    """
    Loads and chunks files into a list of documents then embed
    """

    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    nbr_files = len(json_file_paths)
    st.write(f"Embeding {nbr_files} JSON files...")
    documents = []
    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()   # 1 JSON item per chunk
        print(f"JSON file: {json_file_path}, Number of JSON items: {len(docs)}")
        documents = documents + docs
    st.write(f"Total number of JSON items: {len(documents)}")
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    nbr_files = len(pdf_file_paths)
    st.write(f"Embeding {nbr_files} PDF files...")
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


def assistant_frontend():
    """
    All related to Streamlit and connection with the Langchain backend. Includes also the admin interface.
    """

    st.set_page_config(page_title=ASSISTANT_NAME, page_icon=ASSISTANT_ICON)
    
    # Initialize chat history (chat_history) for LangChain
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)   # Max k Q/A in the chat history for Langchain

    # Initialize chat history (messages) for Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model" not in st.session_state:
        st.session_state.model = "OpenAI (2): gpt-4o-2024-05-13"

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.2

    # Load, index, retrieve and generate

    ai_assistant_chain = instanciate_ai_assistant_chain(st.session_state.model, st.session_state.temperature)

    # # # # # # # #
    # Main window #
    # # # # # # # #

    logo = Image.open(LOGO_PATH)
    st.image(logo, use_column_width=True)

    st.markdown(f"## {ASSISTANT_NAME}")
    st.caption("💬 A chatbot powered by Langchain and Streamlit")

    # # # # # # # # # #
    # Side bar window #
    # # # # # # # # # #

    with st.sidebar:

        password_ok = "no"
        password = "XXXX"
        page = "About"
        # Ask admin password to access admin menu
        admin_password = os.getenv("ADMIN_PASSWORD", "YYYY")
        password = st.text_input("Enter admin password: ", type="password")
        if password != admin_password:
            page = "About"
            password_ok = "no"
        else:
            page = "Admin"
            password_ok = "yes"

        # Side bar: first or second page
        if page == "About":
        
            # # # # # # # # # # # # # # # # # # # #
            # Side bar window: first page (About) #
            # # # # # # # # # # # # # # # # # # # #

            st.write(ABOUT_TEXT)

            st.write(SIDEBAR_FOOTER)

        elif page == "Admin" and password_ok == "yes":

            # # # # # # # # # # # # # # # # # # # # #
            # Side bar window: second page (Admin)  #
            # # # # # # # # # # # # # # # # # # # # #

            model_list = ['OpenAI (2): gpt-4o-2024-05-13', 'OpenAI (1): gpt-4-turbo-2024-04-09', 'Google (2): gemini-1.5-pro-preview-0409', 'Google (1): gemini-1.0-pro-002', 'Anthropic: claude-3-opus-20240229', 'MetaAI: llama3-8b']
            st.session_state.model = st.selectbox('Model: ', model_list)

            st.session_state.temperature = st.slider("Temperature: ", -1.0, 2.0, 0.2)
            st.write("OpenAI: 0 to 2, Anthropic: -1 to 1")
            
            options = ['Scrape Commons', 'Scrape Europeana', 'Embed in DB']
            choice = st.sidebar.radio("Make your choice: ", options)

            if choice == "Scrape Europeana":
                st.write("Give the web page URL of an item from Europeana. The page will be scraped and saved in a JSON file.")
                url = st.text_input("URL: ")
                if url:
                    st.write(f"Scraping the web page...")
                    scrape_europeana_url(url)
                    st.write(f"Web page scraped and saved in a JSON file!")
            elif choice == "Scrape Commons":
                st.write("Give a category name from Wikimedia Commons. The pages will be scraped and saved in a JSON file.")
                category = st.text_input("Category: ")
                if category:
                    st.write(f"Scraping the web pages...")
                    scrape_commons_category(category)
                    st.write(f"Web pages scraped and saved in a JSON file!")
            elif choice == "Embed in DB":
                # Embed data in Chroma DB
                # Load and index

                JSON_FILES_DIR = "./json_files/"
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
                    st.write("Done!")

                if st.button("List Files"):
                    path = './'
                    files = os.listdir(path)
                    st.write("Root path:")
                    st.write(files)
                    path = './chromadb'
                    files = os.listdir(path)
                    st.write("DB path:")
                    st.write(files)
                    file_path = './chromadb/chroma.sqlite3'
                    file_size = os.path.getsize(file_path)
                    st.write(f"DB size: {file_size} bytes")

    # # # # # # # # # # # #
    # Chat message window #
    # # # # # # # # # # # #

    with st.chat_message("assistant"):
        st.write(HELLO_MESSAGE)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if question := st.chat_input(USER_PROMPT):
        # Display user message in chat message container
        st.chat_message("user").markdown(question)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})

        try:

            # Call the main chain (AI assistant). invoke is replaced by stream to stream the answer.
            answer_container = st.empty()
            answer = ""
            for chunk in ai_assistant_chain.stream({"input": question, "chat_history": st.session_state.chat_history}):
                answer_chunk = str(chunk.get("answer"))
                if answer_chunk != "None":  # Because it write NoneNone at the beginning 
                    answer = answer + answer_chunk
                    answer_container.write(answer)

        except Exception as e:
            st.write("Error: Cannot invoke/stream the main chain!")
            st.write(f"Error: {e}")

        # Add Q/A to chat history for Langchain (chat_history)
        st.session_state.chat_history2.save_context({"input": question}, {"output": answer})
        load_memory = st.session_state.chat_history2.load_memory_variables({})
        st.session_state.chat_history = load_memory["history"]

        # Add Answer to chat history for Streamlit (messages)
        st.session_state.messages.append({"role": "assistant", "content": answer})
