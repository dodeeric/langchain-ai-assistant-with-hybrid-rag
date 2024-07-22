#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
This function runs the backend. It starts the Langchain AI assistant: instanciate
all the Langchain chains for RAG and LLM.
"""

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.chains import create_history_aware_retriever  # To create the retriever chain (predefined chain)
from langchain.chains import create_retrieval_chain  # To create the main chain (predefined chain)
from langchain.chains.combine_documents import create_stuff_documents_chain  # To create a predefined chain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
import chromadb
from chromadb.config import Settings
import os

from config.config import *


@st.cache_resource
def instanciate_ai_assistant_chain(model, temperature):
    """
    Instantiate retrievers and chains and return the main chain (AI Assistant).
    Steps: Retrieve and generate.
    """

    try:

        embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)  # 3072 dimensions vectors used to embed the JSON items and the questions

        if CHROMA_SERVER:

            # Run the Chroma server (the app and the db can run on different servers)

            chroma_server_password = os.getenv("CHROMA_SERVER_AUTHN_CREDENTIALS", "YYYY")
            chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT, settings=Settings(chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider", chroma_client_auth_credentials=chroma_server_password))
            #chroma_client = chromadb.HttpClient(host=CHROMA_SERVER_HOST, port=CHROMA_SERVER_PORT)
            vector_db = Chroma(embedding_function=embedding_model, collection_name=CHROMA_COLLECTION_NAME, client=chroma_client)

        else:

            # Save the DB on the local filesystem (the app has to run on the same server)

            vector_db = Chroma(embedding_function=embedding_model, collection_name=CHROMA_COLLECTION_NAME, persist_directory="./chromadb")

        docs = vector_db.get()
        documents = docs["documents"]

    except Exception as e:
        st.write("Error: Cannot instanciate the DB!")
        st.write(f"Error: {e}")        

    # Instanciate the model

    try:

        if model == OLLAMA_MENU:
            llm = ChatOllama(model=OLLAMA_MODEL, temperature=temperature, base_url=OLLAMA_URL)
        elif model == ANTHROPIC_MENU:
            llm = ChatAnthropic(model_name=ANTHROPIC_MODEL, temperature=temperature, max_tokens=4000)
        elif model == VERTEXAI_MENU:
            llm = ChatVertexAI(model_name=VERTEXAI_MODEL, temperature=temperature, max_output_tokens=4000)
        elif model == OPENAI_MENU:
            llm = ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
        elif model == GOOGLE_MENU:
            llm = ChatGoogleGenerativeAI(model=GOOGLE_MODEL, temperature=temperature)
        else:
            st.write("Error: No model available!")
            quit()

    except Exception as e:
        st.write("Error: Cannot instanciate any model!")
        st.write(f"Error: {e}")

    # Instanciate the retrievers

    try:

        vector_retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": VECTORDB_MAX_RESULTS})

        keyword_retriever = BM25Retriever.from_texts(documents)
        keyword_retriever.k = BM25_MAX_RESULTS

        ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vector_retriever], weights=[0.5, 0.5])

    except Exception as e:
        st.write("Error: Cannot instanciate the retrievers! Is the DB available?")
        st.write(f"Error: {e}")

    # Define the prompts

    contextualize_q_system_prompt = CONTEXTUALIZE_PROMPT

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            ("human", "Question: {input}"),
        ]
    )

    if model == OPENAI_MENU:
        qa_system_prompt = SYSTEM_PROMPT
    else:
        qa_system_prompt = SYSTEM_PROMPT2

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            ("human", "Question: {input}"),
        ]
    )

    # Instanciate the chains

    try:

        history_aware_retriever_chain = create_history_aware_retriever(llm, ensemble_retriever, contextualize_q_prompt)
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        ai_assistant_chain = create_retrieval_chain(history_aware_retriever_chain, question_answer_chain)

    except Exception as e:
        st.write("Error: Cannot instanciate the chains!")
        st.write(f"Error: {e}")
        ai_assistant_chain = None

    return ai_assistant_chain
