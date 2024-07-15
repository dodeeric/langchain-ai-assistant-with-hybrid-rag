#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
Miscellaneous functions, including function to chunk and embed files.
"""

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import shutil
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
import os

from config.config import *


def load_files_and_embed(json_file_paths: list, pdf_file_paths: list, embed: bool) -> None:
    """
    Loads and chunks files into a list of documents then embed
    """

    try:

        embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

        nbr_files = len(json_file_paths)
        st.write(f"Number of JSON files: {nbr_files}")
        documents = []
        for json_file_path in json_file_paths:
            loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
            docs = loader.load()   # 1 JSON item per chunk
            print(f"JSON file: {json_file_path}, Number of web pages: {len(docs)}")
            documents = documents + docs
        st.write(f"Number of web pages: {len(documents)}")
        if embed:
            st.write('Create DB client...')
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            chroma_server_password = os.getenv("CHROMA_SERVER_AUTHN_CREDENTIALS", "YYYY")
            chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT, settings=Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider", chroma_client_auth_credentials=chroma_server_password))
            st.write('Write web pages in DB...')
            Chroma.from_documents(documents, embedding=embedding_model, collection_name=CHROMA_COLLECTION_NAME, client=chroma_client)
            st.write('Write in DB: done')

        nbr_files = len(pdf_file_paths)
        st.write(f"Number of PDF files: {nbr_files}")
        documents2 = []
        if pdf_file_paths:  # if equals to "", then skip
            for pdf_file_path in pdf_file_paths:
                loader = PyPDFLoader(pdf_file_path)
                pages = loader.load_and_split()  # 1 pdf page per chunk
                print(f"PDF file: {pdf_file_path}, Number of PDF pages: {len(pages)}")
                documents2 = documents2 + pages
        st.write(f"Number of PDF pages: {len(documents2)}")
        st.write(f"Number of web and pdf pages: {len(documents) + len(documents2)}")
        if embed:
            st.write('Write pdf pages in DB...')
            Chroma.from_documents(documents2, embedding=embedding_model, collection_name=CHROMA_COLLECTION_NAME, client=chroma_client)
            st.write('Write in DB: done')

    except Exception as e:
        st.write("Error: The Chroma vector DB is not available locally. Is it running on a remote server?")
        st.write(f"Error: {e}")


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
