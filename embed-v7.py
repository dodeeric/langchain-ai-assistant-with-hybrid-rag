#!/usr/bin/env python

# v4: embed all JSON files from a given directory
# v5: re-adding pdf indexation
# v6: XML (RDF/JSON) indexation
# v7: for XML (RDF/JSON) indexation, do it per batches

import dotenv, jq, os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# For RDF/XML
import json
from langchain.schema import Document
from rdflib import Graph
import warnings
import logging

# Suppress all warnings
warnings.filterwarnings("ignore")

# Log errors in a file and do not display them
logging.basicConfig(filename='error.log', level=logging.ERROR)

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "bmae"

def load_files_and_embed(json_file_paths, pdf_file_paths, xml_file_paths):
    # Loads and chunks files into a list of documents then embed

    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    documents = []
    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()   # 1 JSON item per chunk
        documents = documents + docs
    vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    documents = []
    if pdf_file_paths:   # if equals to "", then skip
        for pdf_file_path in pdf_file_paths:
            loader = PyPDFLoader(pdf_file_path)
            pages = loader.load_and_split() # 1 pdf page per chunk
            documents = documents + pages
    vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    # Valid only for RDF/XML from IRPA BALaT
    documents = []
    if xml_file_paths:   # if equals to "", then skip
        j = 1
        for xml_file_path in xml_file_paths:

            print(f"(B)>>> j: {j}")
            j = j + 1
            
            print(f"(1)>>> xml_file_path: {xml_file_path}")
            
            g = Graph()
            g.parse(xml_file_path, format="xml")

            # Search image url
            for index, (sub, pred, obj) in enumerate(g):
                if sub.startswith("http://balat.kikirpa.be/image/thumbnail/") and ("image/jpeg" in obj):
                    print(f"(1b)>>>sub: {sub}")
                    og_image = sub

            print(f"(2)>>> og_image: {og_image}")
            
            # Search image page url and image details 
            query = """
            SELECT ?s ?title ?creator ?date ?format ?type ?medium ?description
            WHERE {
              ?s <http://purl.org/dc/elements/1.1/title> ?title.
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/date> ?date. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/description> ?description. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/creator> ?creator. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/format> ?format. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/type> ?type. }
              OPTIONAL { ?s <http://purl.org/dc/terms/medium> ?medium. }  
            }
            """

            for row in g.query(query):
                url = row.s
                title = row.title
                creator = row.creator if row.creator else ''
                date = row.date if row.date else ''
                format = row.format if row.format else ''
                type = row.type if row.type else ''
                medium = row.medium if row.medium else ''
                description = row.description if row.description else ''

            item = {
                "url": url,
                "og:image": og_image,
                "titel": title,
                "creator":  creator,
                "date": date,
                "format": format,
                "type": type,
                "medium": medium,
                "description": description
            }

            doc = json.dumps(item)   # JSON string type
            print(f"(4)>>> doc (json string): {doc}")
            document = Document(page_content=doc)   # Document type
            documents.append(document)   # list of Document type

    vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    return vector_db

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

# RDF/XML files
xml_files = os.listdir("/root/download.europeana.eu/dataset/XML/")
xml_paths = []
i = 1
for xml_file in xml_files:
    print(f">>> {i}")
    i = i + 1
    xml_path = f"/root/download.europeana.eu/dataset/XML/{xml_file}"
    if i < 25:
        xml_paths.append(xml_path)

vectordb = load_files_and_embed(paths, pdf_paths, xml_paths)
