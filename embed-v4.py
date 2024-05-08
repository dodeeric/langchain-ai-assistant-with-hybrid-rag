#!/usr/bin/env python

# v4: embed all the files from a given directory

import dotenv, jq, os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "bmae"

def load_files(json_file_paths, pdf_file_paths):
    # Loads and chunks files into a list of documents

    print(f">>>>1>>>> {json_file_paths}")

    documents = []

    for json_file_path in json_file_paths:
        print(f">>>>2>>>> {json_file_path}")
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load() # 1 JSON item per chunk
        documents = documents + docs

#    for pdf_file_path in pdf_file_paths:
#        loader = PyPDFLoader(pdf_file_path)
#        pages = loader.load_and_split() # 1 pdf page per chunk
#        documents = documents + pages
    
    return documents

# Load and index

#json_file_path1 = "./files/commons-urls-ds1-swp.json"
#json_file_path2 = "./files/balat-urls-ds1-swp.json"
#json_file_path3 = "./files/belgica-urls-ds1-swp.json"
#json_file_path4 = "./files/commons-urls-ds2-swp.json"
#json_file_path5 = "./files/balat-urls-ds2-swp.json"
#json_file_paths = [json_file_path1, json_file_path2, json_file_path3, json_file_path4, json_file_path5]

#pdf_file_path1 = "./files/cdf-fxw.pdf"
#pdf_file_paths = [pdf_file_path1]

# Specify the directory you want to list
directory_path = './files/'

# List all files and directories in the specified directory
all_items = os.listdir(directory_path)

# Filter out directories, keep only files
files = [item for item in all_items if os.path.isfile(os.path.join(directory_path, item))]

# Print the list of files
for file in files:
    path = f"./files/{file}"
    print(path)
    documents = load_files(path, "")
    ##embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    ##vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
