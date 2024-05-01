import dotenv, jq
import streamlit as st
from langchain import hub
from langchain_community.document_loaders import JSONLoader
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

dotenv.load_dotenv()

# Index

file_path1 = "./commons-urls-ds1-swp.json"
file_path2 = "./balat-ds1c-wcc-cheerio-ex_2024-04-06_09-05-15-262.json"
file_path3 = "./belgica-ds1c-wcc-cheerio-ex_2024-04-06_08-30-26-786.json"
file_path4 = "./commons-urls-ds2-swp.json"
file_path5 = "./balat-urls-ds2-swp.json"
file_paths = [file_path1, file_path2, file_path3, file_path4, file_path5]

documents = []
for file_path in file_paths:
    loader = JSONLoader(file_path=file_path, jq_schema=".[]", text_content=False)
    docs = loader.load()
    documents = documents + docs

collection_name = "bmae-json"
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
vector_db = Chroma.from_documents(documents, embedding_model, collection_name=collection_name, persist_directory="./chromadb")
