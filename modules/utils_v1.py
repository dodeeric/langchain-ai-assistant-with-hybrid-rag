#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
Miscellaneous functions, including function to chunk and embed files.
"""

# v1: move 2 functions from assistant_frontend_v6.py

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import shutil
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
#import chromadb

from config.config import *


def load_files_and_embed(json_file_paths: int, pdf_file_paths: int, embed: bool) -> None:
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
            Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            #Chroma(documents, embedding_function=embedding_model, collection_name=COLLECTION_NAME, client=chroma_client)

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
            Chroma.from_documents(documents2, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            #Chroma(documents2, embedding_function=embedding_model, collection_name=COLLECTION_NAME, client=chroma_client)

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
