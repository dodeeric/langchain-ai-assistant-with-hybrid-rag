#!/usr/bin/env python

"""
This subpage runs the admin web interface.
"""

import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
import os

from modules.web_scraping_utils_v1 import scrape_commons_category, scrape_web_page_url
from modules.utils_v1 import load_files_and_embed, delete_directory
from config.config import *


def reset_conversation():
    """
    Reset the conversation: clear the chat history and clear the screen.
    """

    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)


st.title("Admin")

st.sidebar.write(f"Model: {st.session_state.model} ({st.session_state.temperature})")

# Ask admin password to access admin menu
admin_password = os.getenv("ADMIN_PASSWORD", "YYYY")
password = st.sidebar.text_input("Enter admin password: ", type="password")
if password != admin_password:
    st.session_state.password_ok = False
else:
    st.session_state.password_ok = True

if st.session_state.password_ok:

    # # # # # # # # # # # # # # # # # # # # #
    # Side bar window: second page (Admin)  #
    # # # # # # # # # # # # # # # # # # # # #
    
    options = ['Upload PDF Files', 'Scrape Web Pages', 'Scrape Web Pages from Wikimedia Commons', 'Embed Pages in DB', 'Model and Temperature', 'Upload Files']
    choice = st.sidebar.radio("Make your choice: ", options)

    if choice == "Scrape Web Pages":
        st.caption("Give the web page URL and the filter (CSS class). The page will be scraped and saved in a JSON file.")
        st.caption("""
                    Filter: 
                    - two-third last (balat / irpa)
                    - media-body (belgica / kbr)
                    - hproduct commons-file-information-table (commons / wikimedia: summary or description section)
                    - card metadata-box-card mb-3 (europeana / kul, irpa, etc.)
                    """)
        url = st.text_input("URL: ")
        filter = st.text_input("Filter: ")
        if url and filter:
            st.write(f"Scraping the web page...")
            scrape_web_page_url(url, filter)
            st.write(f"Web page scraped and saved in a JSON file!")

    elif choice == "Model and Temperature":
        st.caption("Change temporarily the model and the temperature.")
        model_list = [OPENAI_MENU, ANTHROPIC_MENU, VERTEXAI_MENU, OLLAMA_MENU]
        st.session_state.model = st.selectbox('Model: ', model_list, DEFAULT_MENU_CHOICE)
        st.session_state.temperature = st.slider("Temperature: ", 0.0, 2.0, DEFAULT_TEMPERATURE)
        st.caption("OpenAI: 0-2, Anthropic: 0-1")

    elif choice == "Scrape Web Pages from Wikimedia Commons":
        st.caption("Give a category name from Wikimedia Commons. The pages will be scraped and saved in a JSON file.")
        category = st.text_input("Category: ")
        if category:
            st.write(f"Scraping the web pages...")
            scrape_commons_category(category)
            st.write(f"Web pages scraped and saved in a JSON file!")

    elif choice == "Upload Files":
        st.caption("Upload a file in the 'root' directory.")
        uploaded_file = st.file_uploader("Choose a file:")
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            file_name = uploaded_file.name
            with open(file_name, "wb") as file:
                file.write(bytes_data)
            st.success(f"File '{file_name}' uploaded and saved successfully!")
        else:
            st.warning("No file uploaded yet.")

    elif choice == "Upload PDF Files":
        st.caption("Upload a PDF file in the 'pdf_files' directory.")
        uploaded_file = st.file_uploader("Choose a PDF file:", type=["pdf"])
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            file_name = uploaded_file.name
            with open(f"./pdf_files/{file_name}", "wb") as file:
                file.write(bytes_data)
            st.success(f"File '{file_name}' uploaded and saved successfully!")
        else:
            st.warning("No file uploaded yet.")  

    elif choice == "Embed Pages in DB":
        # Embed data in Chroma DB
        # Load and index

        st.caption('Embed in the vector DB all the web and pdf pages.')

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
            load_files_and_embed(json_paths, pdf_paths, embed=True)
            st.write("Done!")

        if st.button("Delete DB"):
            delete_directory("./chromadb")
            st.write("Done!")

        if st.button("Clear Memory and Streamlit Cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            reset_conversation()
            st.write("Done!")

        if st.button("Files and DB Info"):

            load_files_and_embed(json_paths, pdf_paths, embed=False)

            try:

                file_path = './chromadb/chroma.sqlite3'
                file_size = os.path.getsize(file_path)
                file_size = file_size / 1024  # In KB
                if file_size > 144:
                    st.write(f"DB size: {file_size} KB")
                else:
                    st.write(f"DB size: {file_size} KB. DB is empty!")

                path = './'
                files = os.listdir(path)
                st.write("Root path:")
                st.write(files)

                path = './chromadb'
                files = os.listdir(path)
                st.write("DB path:")
                st.write(files)

            except Exception as e:
                st.write("Error: Is the DB available?")
                st.write(f"Error: {e}")
