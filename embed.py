#!/usr/bin/env python

# v31: with PDF indexation, with function

import dotenv, jq
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "bmae"

def load_files(json_file_paths, pdf_file_paths):
    # Loads and chunks files into a list of documents

    documents = []

    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load() # 1 JSON item per chunk
        documents = documents + docs

    for pdf_file_path in pdf_file_paths:
        loader = PyPDFLoader(pdf_file_path)
        pages = loader.load_and_split() # 1 pdf page per chunk
        documents = documents + pages
    
    return documents

# Load and index

json_file_path1 = "./files/commons-urls-ds1-swp.json"
json_file_path2 = "./files/balat-urls-ds1-swp.json"
json_file_path3 = "./files/belgica-urls-ds1-swp.json"
json_file_path4 = "./files/commons-urls-ds2-swp.json"
json_file_path5 = "./files/balat-urls-ds2-swp.json"
json_file_paths = [json_file_path1, json_file_path2, json_file_path3, json_file_path4, json_file_path5]

pdf_file_path1 = "./files/BPEB31_DOS4_42-55_FR_LR.pdf"
pdf_file_paths = [pdf_file_path1]

documents = load_files(json_file_paths, pdf_file_paths)

embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
vector_db = Chroma.from_documents(documents, embedding_model, collection_name=EMBEDDING_MODEL, persist_directory="./chromadb")
