#!/usr/bin/env python

"""
This function runs the backend. It starts the Langchain AI assistant: instanciate
all the Langchain chains for RAG and LLM.
"""

# v2: add temperature as a variable + catch errors + use langchain-google-vertexai package + parameters in config.py

import streamlit as st
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever  # To create the retriever chain (predefined chain)
from langchain.chains import create_retrieval_chain  # To create the main chain (predefined chain)
from langchain.chains.combine_documents import create_stuff_documents_chain  # To create a predefined chain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from config.config import *

@st.cache_resource
def instanciate_ai_assistant_chain(model, temperature):
    """
    Instantiate retrievers and chains and return the main chain (AI Assistant).
    Steps: Retrieve and generate.
    """

    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)  # 3072 dimensions vectors used to embed the JSON items and the questions
    vector_db = Chroma(embedding_function=embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
    docs = vector_db.get()
    documents = docs["documents"]

    # Instanciate the model

    try:

        if model == "MetaAI: llama3-8b":
            llm = ChatOllama(model=OLLAMA_MODEL, temperature=temperature, base_url="http://104.248.246.235:80")  # base_url="http://localhost:11434"
        elif model == "Anthropic: claude-3-opus-20240229":
            llm = ChatAnthropic(model_name=ANTHROPIC_MODEL, temperature=temperature, max_tokens=4000)
        elif model == "Google (1): gemini-1.0-pro-002":
            llm = ChatVertexAI(model_name=VERTEXAI_MODEL, temperature=temperature, max_output_tokens=4000)
        elif model == "Google (2): gemini-1.5-pro-preview-0409":
            llm = ChatVertexAI(model_name=VERTEXAI_MODEL2, temperature=temperature, max_output_tokens=4000)
        elif model == "OpenAI (1): gpt-4-turbo-2024-04-09":
            llm = ChatOpenAI(model=OPENAI_MODEL, temperature=temperature)
        elif model == "OpenAI (2): gpt-4o-2024-05-13":
            llm = ChatOpenAI(model=OPENAI_MODEL2, temperature=temperature)
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

    contextualize_q_system_prompt = CONTEXT_PROMPT

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            ("human", "Question: {input}"),
        ]
    )

    if model == "OpenAI (1): gpt-4-turbo-2024-04-09" or model == "OpenAI (2): gpt-4o-2024-05-13":
        qa_system_prompt = PROMPT1
    else:
        qa_system_prompt = PROMPT2

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            ("human", "Question: {input}"),
        ]
    )

    # Instanciate the chains

    try:

        history_aware_retriever = create_history_aware_retriever(llm, ensemble_retriever, contextualize_q_prompt)
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        ai_assistant_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    except Exception:
        st.write("Error: Cannot instanciate the chains!")
        ai_assistant_chain = None

    return ai_assistant_chain
