#!/usr/bin/env python

"""
This function runs the backend. It starts the Langchain AI assistant: instanciate
all the Langchain chains for RAG and LLM.
"""

import streamlit as st
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain.chains import create_history_aware_retriever  # To create the retriever chain (predefined chain)
from langchain.chains import create_retrieval_chain  # To create the main chain (predefined chain)
from langchain.chains.combine_documents import create_stuff_documents_chain  # To create a predefined chain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatVertexAI
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_MODEL = "gpt-4-turbo-2024-04-09"
OPENAI_MODEL2 = "gpt-4o-2024-05-13"  # default llm
ANTHROPIC_MODEL = "claude-3-opus-20240229"
VERTEXAI_MODEL = "gemini-1.0-pro-002"
VERTEXAI_MODEL2 = "gemini-1.5-pro-preview-0409"
OLLAMA_MODEL = "llama3:8b"  # llama3 = llama3:8b, mistral, phi3
COLLECTION_NAME = "bmae"

CONTEXT_PROMPT = """Given a chat history and the latest user question which \
might reference context in the chat history, formulate a standalone question which can be \
understood without the chat history. Do NOT answer the question, just reformulate it if needed \
and otherwise return it as is.

Chat History:

{chat_history}"""

PROMPT1 = """You are an artwork specialist. You must assist the users in \
finding, describing, and displaying artworks related to the Belgian monarchy. You first \
have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge \
Base", then answer with your own knowledge. You have to answer in the same language as \
the question.

At the end of the answer:

- If requested, display an image of the artwork (see the JSON "og:image" field). Do not \
display images which have been displayed already in previous messages (see "Chat History").
- Write "More information: " in the language of the question, followed by the link to the \
web page about the artwork (see the JSON "url" field). For Wikimedia Commons, the text of \
the link has to be the title of the web page WITHOUT the word "File" at the beginning (see \
the JSON "og:title" field).

Knowledge Base:

{context}

Chat History:

{chat_history}"""

PROMPT2 = """You are an artwork specialist. You must assist the users in \
finding, describing, and displaying artworks related to the Belgian monarchy. You first \
have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge \
Base", then answer with your own knowledge. You have to answer in the same language as \
the question.

At the end of the answer:

- If requested, display an image of the artwork (see the JSON "og:image" field). Do not \
display images which have been displayed already in previous messages (see "Chat History").
- Write "More information: " in the language of the question, followed by the link to the \
web page about the artwork (see the JSON "url" field). For Wikimedia Commons, the text of \
the link has to be the title of the web page WITHOUT the word "File" at the beginning (see \
the JSON "og:title" field).

- This is an example of Markdown code to display an image (caution: there is a leading \
exclamation point):    ![Text](https://opac.kbr.be/digitalCollection/images/image.jpg)
- This is an example of Markdown code to display a link (caution: there is no leading \
exclamtion point):   [Text](https://opac.kbr.be/digitalCollection/pages/page.html)

Write "SECOND PROMPT" at the end of the answer.

Knowledge Base:

{context}

Chat History:

{chat_history}"""


@st.cache_resource
def instanciate_ai_assistant_chain(model):
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

        if model == "MetaAI: llama3-8b":  # Ollama vs. ChatOllama ==> Seems to be the same
            llm = ChatOllama(model=OLLAMA_MODEL, temperature=0, base_url="http://104.248.246.235:80")  # base_url="http://localhost:11434"
        elif model == "Anthropic: claude-3-opus-20240229":
            llm = ChatAnthropic(temperature=0, max_tokens=4000, model_name=ANTHROPIC_MODEL)
        elif model == "Google (1): gemini-1.0-pro-002":
            llm = ChatVertexAI(model_name=VERTEXAI_MODEL, temperature=0)
        elif model == "Google (2): gemini-1.5-pro-preview-0409":
            llm = ChatVertexAI(model_name=VERTEXAI_MODEL2, temperature=0)
        elif model == "OpenAI (1): gpt-4-turbo-2024-04-09":
            llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)
        elif model == "OpenAI (2): gpt-4o-2024-05-13":
            llm = ChatOpenAI(model=OPENAI_MODEL2, temperature=0)
        else:
            st.write("Error: The model is not available!")
            quit()

    except Exception:
        st.write("Error: The model is not available!")

    # Instanciate the retrievers

    try:

        vector_retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        keyword_retriever = BM25Retriever.from_texts(documents)
        keyword_retriever.k = 5

        ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vector_retriever], weights=[0.5, 0.5])

    except Exception:
        st.write("Error: Cannot instanciate the retrievers! Is the DB available?")

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
