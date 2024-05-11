#!/usr/bin/env python

# v4: embed all JSON files from a given directory
# v5: re-adding pdf indexation
# v6: XML (RDF/JSON) indexation
# v7: for XML (RDF/JSON) indexation, do it per batches
# v8: for XML (RDF/JSON) indexation, do it per batches, move XML in another function
# v1: only JSON/PDF
# v2: small enhancements

import dotenv, jq, os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

dotenv.load_dotenv()

def load_files_and_embed(json_file_paths, pdf_file_paths):
    # Loads and chunks files into a list of documents then embed

    EMBEDDING_MODEL = "text-embedding-3-large"
    COLLECTION_NAME = "bmae"
    JSON_FILES_DIR = "./files/"
    PDF_FILES_DIR = "./pdf_files/"
    
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    nbr_files = len(json_file_paths)
    print(f">>> Embed {nbr_files} JSON files...")
    documents = []
    for json_file_path in json_file_paths:
        print(f">>> JSON file: {json_file_path}")
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()   # 1 JSON item per chunk
        documents = documents + docs
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    nbr_files = len(pdf_file_paths)
    print(f">>> Embed {nbr_files} PDF files...")
    documents = []
    if pdf_file_paths:   # if equals to "", then skip
        for pdf_file_path in pdf_file_paths:
            print(f">>> PDF file: {pdf_file_path}")
            loader = PyPDFLoader(pdf_file_path)
            pages = loader.load_and_split() # 1 pdf page per chunk
            documents = documents + pages
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    return "JSON/PDF file done"

# Load and index

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

load_files_and_embed(json_paths, pdf_paths)
