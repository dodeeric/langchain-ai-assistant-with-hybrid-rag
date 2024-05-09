#!/usr/bin/env python

# v4: embed all JSON files from a given directory
# v5: re-adding pdf indexation 

import dotenv, jq, os
from langchain_community.document_loaders import JSONLoader
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
        docs = loader.load()   # 1 JSON item per chunk
        documents = documents + docs

    if pdf_file_paths:
        for pdf_file_path in pdf_file_paths:
            loader = PyPDFLoader(pdf_file_path)
            pages = loader.load_and_split() # 1 pdf page per chunk
            documents = documents + pages

    return documents

# Load and index

# JSON files
files = os.listdir("./files/")
paths = []
for file in files:
    path = f"./files/{file}"
    paths.append(path)

# PDF files
pdf_files = os.listdir("./pdf_files/")
pdf_paths = []
for pdf_file in pdf_files:
    pdf_path = f"./pdf_files/{pdf_file}"
    pdf_paths.append(pdf_path)

documents = load_files(paths, pdf_paths)

embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
