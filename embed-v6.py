#!/usr/bin/env python

# v4: embed all JSON files from a given directory
# v5: re-adding pdf indexation
# v6: XML (RDF/JSON) indexation

import dotenv, jq, os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# For RDF/XML
import json
from langchain.schema import Document
from rdflib import Graph
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "bmae"

def load_files(json_file_paths, pdf_file_paths, xml_file_paths):
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

    # Valid only for RDF/XML from IRPA BALaT
    if xml_file_paths:
        for xml_file_path in xml_file_paths:

            print(f">>> xml_file_path: {xml_file_path}")
            
            g = Graph()
            g.parse(xml_file_path, format="xml")

            # Search image url
            for index, (sub, pred, obj) in enumerate(g):
                if sub.startswith("http://balat.kikirpa.be/image/thumbnail/") and ("image/jpeg" in obj):
                    og_image = sub

            # Search image page url and image details 
            query = """
            SELECT ?s ?title ?creator ?date ?description
            WHERE {
              ?s <http://purl.org/dc/elements/1.1/title> ?title.
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/date> ?date. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/description> ?description. }
              OPTIONAL { ?s <http://purl.org/dc/elements/1.1/creator> ?creator. }
            }
            """

            for row in g.query(query):
                url = row.s
                title = row.title if row.title else ''
                description = row.description if row.description else ''
                date = row.date if row.date else ''
                creator = row.creator if row.creator else ''
                print(f">>> url: {url}, title: {title}, creator: {creator}, date: {date}, description: {description}, og:image: {og_image}")

            item = {   # dict type
                "url": url,
                "og:image": og_image,
                "creator":  creator,
                "date": date,
                "description": description
            }

            doc = json.dumps(item)   # string type
            document = Document(page_content=doc)   # Document type
            documents.append(document)

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

# RDF/XML files
xml_files = os.listdir("/root/download.europeana.eu/dataset/XML/")
xml_paths = []
for xml_file in xml_files:
    print(f">>> xml_file: {xml_file}")
    xml_path = f"/root/download.europeana.eu/dataset/XML/{xml_file}"
    print(f">>> xml_path: {xml_path}")
    xml_paths.append(xml_path)

documents = load_files(paths, pdf_paths, xml_paths)

embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
vector_db = Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
