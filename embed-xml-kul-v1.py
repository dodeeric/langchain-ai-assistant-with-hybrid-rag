#!/usr/bin/env python

# v4: embed all JSON files from a given directory
# v5: re-adding pdf indexation
# v6: XML (RDF/JSON) indexation
# v7: for XML (RDF/JSON) indexation, do it per batches
# v8: for XML (RDF/JSON) indexation, do it per batches, move XML in another function
# v1: only XML for KUL (via Europeana) (convert RDF/XML into custom JSON: url: page url, og:image: image url, dc:xxx)

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

def load_files_and_embed_xml():
    # Loads and chunks files into a list of documents then embed
    # Valid only for RDF/XML from Europeana for KUL

    EMBEDDING_MODEL = "text-embedding-3-large"
    COLLECTION_NAME = "bmae"
    BATCH_SIZE = 100
    
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    xml_files = os.listdir("/root/download.europeana.eu/dataset/XML-KUL/")   # All the XML files
  
    xml_paths = []   # Will hold all the XML files (absolute path)
    for xml_file in xml_files:
        xml_path = f"/root/download.europeana.eu/dataset/XML-KUL/{xml_file}"
        xml_paths.append(xml_path)

    nbr_files = len(xml_paths)
    nbr_batches = int(len(xml_paths) / BATCH_SIZE)   # Ex: batches of 100 files; up to 100 last files could be not processed 

    print(f">>> Embed {nbr_files} RDF/XML files...")
    
    for j in range(nbr_batches):   # j = batch id: from 0 to nbr_batches-1, i = file id in the batch: 0 to BATCH_SIZE-1
        documents = []
        for i in range(BATCH_SIZE):
            xml_path = xml_paths[j+i]
            g = Graph()
            g.parse(xml_path, format="xml")
            # Search image url
            for index, (sub, pred, obj) in enumerate(g):
                if sub.startswith("https://lib.is/") and ("image/jpeg" in obj):
                    og_image = sub
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
                "title": title,
                "creator":  creator,
                "date": date,
                "format": format,
                "type": type,
                "medium": medium,
                "description": description
            }
            doc = json.dumps(item)   # JSON string type
            document = Document(page_content=doc)   # Document type
            print(f">>> Batch: {j}/{nbr_batches}, File: {i+(j*BATCH_SIZE)}/{nbr_files}")
            documents.append(document)   # list of Document type
        Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    return "RDF/XML files done"

# Load and index

load_files_and_embed_xml()
