#!/usr/bin/env python

"""
Miscealinous functions.
"""

# v1: move 2 functions from assistant_frontend_v6.py

import streamlit as st
import shutil
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from config.config import *


def load_files_and_embed(json_file_paths: int, pdf_file_paths: int) -> None:
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
