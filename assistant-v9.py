#!/usr/bin/env python

# v2: with chat history
# v3: with PDF indexation
# v31/v32: JSON and PDF indexation with function
# v5: with a limit of messages in the chat history
# v6: load chunks only from DB on disk
# v7: diplay question examples in the expander
# v8: ollama (llama3, mistral, etc.) + anthropic claude + google vertexai
# v9: multiselect box to chose the model

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art  #
# and the Belgian monarchy. To answer, the assistant queries the graphic databases BALaT of the IRPA  #
# (Royal Institute of Artistic Heritage), Belgica of the KBR (Royal Library) and Wikimedia Commons.   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import dotenv, jq, time
import streamlit as st
from PIL import Image
from langchain_community.document_loaders import JSONLoader
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_history_aware_retriever # To create the retriever chain (predefined chain)
from langchain.chains import create_retrieval_chain # To create the main chain (predefined chain)
from langchain.chains.combine_documents import create_stuff_documents_chain # To create a predefined chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import VertexAI
from langchain_community.llms import Ollama

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_MODEL = "gpt-4-turbo-2024-04-09"
CLAUDE_MODEL = "claude-3-opus-20240229"
VERTEXAI_MODEL = "gemini-1.5-pro-preview-0409"   # "gemini-1.0-pro-002"
OLLAMA_MODEL = "llama3"   # "mistral" # "phi3"
COLLECTION_NAME = "bmae"

model = "OpenAI: gpt-4-turbo-2024-04-09"

@st.cache_resource
def instanciate_vector_db():
    # Instantiates Vector DB
    
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL) # 3072 dimensions vectors used to embed the JSON items and the questions
    vector_db = Chroma(embedding_function=embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")
        
    return vector_db

@st.cache_resource
def instanciate_retrievers_and_chains(_vector_db, model):
    # Instantiate retrievers and chains and return the main chain (AI Assistant)
    # Retrieve and generate

    docs = vector_db.get()
    documents = docs["documents"]

    if model == "MetaAI: llama3-8b":
        llm = Ollama(model=OLLAMA_MODEL, temperature=0, base_url="http://35.209.146.25:80")   # base_url="http://localhost:11434"
    elif model == "Anthropic: claude-3-opus-20240229":
        llm = ChatAnthropic(temperature=0, max_tokens=4000, model_name=CLAUDE_MODEL)
    elif model == "Google: gemini-1.5-pro-preview-0409":
        llm = VertexAI(model_name=VERTEXAI_MODEL, temperature=0)
    else:
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)

    st.write(">>> Model (inside function): ", model)
    
    vector_retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    keyword_retriever = BM25Retriever.from_texts(documents)
    keyword_retriever.k = 5

    ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vector_retriever], weights=[0.5, 0.5])

    contextualize_q_system_prompt = """
    Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is.

    Chat History:

    {chat_history}
    """

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            ("human", "Question: {input}"),
        ]
    )
    
    history_aware_retriever = create_history_aware_retriever(
        llm, ensemble_retriever, contextualize_q_prompt 
    )

    qa_system_prompt = """
    You are an artwork specialist. You must assist the users in finding, describing, and displaying artworks related to the Belgian monarchy. \
    You first have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge Base", then answer with your own knowledge. \
    You have to answer in the same language as the question.
    At the end of the answer:
    - At a new line, display an image of the artwork (see the "og:image" field).
    - At a new line, write "More information: " (in the language of the question) followed by the link to the web page about the artwork (see the "url" field). \
    For Wikimedia Commons, the text of the link has to be the title of the web page WITHOUT the word "File" at the beginning (see "og:title").

    To display an image, use the following Markdown code: ![Image](<replace with the "og:image" url of the image>). Do not display an image which has been displayed already (see "Chat History").
    To display a link, use the following Markdow code: [Link](<replace with the "url" of the web page>).

    Knowledge Base:

    {context}

    Chat History:

    {chat_history}
    """

    qa_system_prompt_OPENAI = """
    You are an artwork specialist. You must assist the users in finding, describing, and displaying artworks related to the Belgian monarchy. \
    You first have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge Base", then answer with your own knowledge. \
    You have to answer in the same language as the question.
    At the end of the answer:
    - At a new line, display an image of the artwork (see the "og:image" field).
    - At a new line, write "More information: " (in the language of the question) followed by the link to the web page about the artwork (see the "url" field). \
    For Wikimedia Commons, the text of the link has to be the title of the web page WITHOUT the word "File" at the beginning (see "og:title").

    Knowledge Base:

    {context}

    Chat History:

    {chat_history}
    """

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            ("human", "Question: {input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    ai_assistant_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return ai_assistant_chain

# Load, index, retrieve and generate

vector_db = instanciate_vector_db()

st.write(">>> Model (before calling function): ", model)
ai_assistant_chain = instanciate_retrievers_and_chains(vector_db, model)

# Streamlit

with st.expander("Examples of questions you can ask | Exemples de questions que vous pouvez poser"):
    
    st.markdown("""
    
    ENGLISH:
    
    - When did King Leopold I die? Do you have any images of the funeral?
    - Do you have any images of Queen Elizabeth during the First World War?
    - Can you show me the canvas "The school review"? *And then you can ask the question:*
    - Who painted this canvas? *And then again:*
    - What is the size of the canvas? *And then again:*
    - Who is present on this canvas? *And then again:*
    - Can you show me this canvas with a photo from Wikimedia Commons and another photo from BALaT?
    - When did the fire at Laeken Castle take place? Do you have images of this event?
    - When did King Leopold I get married? *The assistant will show you an image of the wedding.*
    - Can you show me a portrait of King Leopold I? It has to be an engraving.
    - Can you show me images of King Leopold II?
    - Can you show me images of King Leopold II during his accession to the throne in 1865?
    - Do you have works created by Aimable Dutrieux? *And then you can ask the question:*
    - Who was this sculptor?
    - Can you show me images of Queen Marie-Henriette? Can you give me the authors of the images?
    - Can you show me the painting "The patriotic celebration of Belgium's fiftieth anniversary" created by Camille Van Camp?
    - Who are the people present in this painting?
    - Can you show me two engravings of the patriotic celebration of the fiftieth anniversary of Belgium created by Martin Claverie? From which newspapers do they come from?
    """)

    st.markdown("""
    
    FRANCAIS:

    - Quand est mort le roi Léopold Ier ? Avez-vous des images des funérailles ?
    - Avez-vous des images de la reine Elisabeth pendant la Premierre Guerre mondiale ?
    - Pouvez-vous me montrer le tableau "La revue des écoles" ? *Et ensuite vous pouvez poser la question :*
    - Qui a peint ce tableau ? *Et encore ensuite :*
    - Quelle est la dimension du tableau ? *Et encore ensuite :*
    - Qui est présent sur le tableau ? *Et encore ensuite :*
    - Pouvez-vous me montrer ce tableau avec une photo de la Wikimedia Commons et une autre photo de BALaT ?
    - Quand a eu lieu l'incendie du château de Laeken ? Avez-vous plusieurs images de cet événement ?
    - Quand s'est marié le roi Léopold Ier ? *L'assistant vous montrera une image du mariage.*
    - Pouvez-vous me montrer un portrait du roi Léopold Ier ? Il faut que ce soit une gravure.
    - Pouvez-vous me montrer plusieurs images du roi Léopold II ?
    - Pouvez-vous me montrer des images du roi Léopold II lors de son avènement en 1865 ?
    - Avez-vous des oeuvres réalisées par Aimable Dutrieux ? *Et ensuite vous pouvez poser la question :*
    - Qui était ce sculteur ?
    - Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?
    - Pouvez-vous me montrer le tableau "La fête patriotique du cinquantenaire de la Belgique" réalisé par Camille Van Camp ?
    - Quelles sont les personnes présentes sur ce tableau ?
    - Pouvez-vous me montrer deux gravures de la fête patriotique du cinquantenaire de la Belgique réalisées par Martin Claverie ? De quel journal proviennent-elles ?
    """)

logo = Image.open("./crown.jpg")
st.image(logo, use_column_width=True)

#st.set_page_config(page_title="BMAE", page_icon="👑")
#st.title("Belgian Monarchy Artworks Explorer")
st.markdown("## Belgian Monarchy Artworks Explorer")
st.caption("💬 A chatbot powered by OpenAI, Langchain and Streamlit")

model_list = ['OpenAI: gpt-4-turbo-2024-04-09', 'Google: gemini-1.5-pro-preview-0409', 'Anthropic: claude-3-opus-20240229', 'MetaAI: llama3-8b']
model = st.selectbox('Choose a model | Choisissez un modèle | Kies een model: ', model_list)
st.write('You selected | Vous avez sélectionné | Jij hebt geselecteerd: ', model)

with st.sidebar:

    st.markdown("""
    ### About this assistant
    
    This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art and the Belgian monarchy. To answer, the assistant \
    queries different images databases like BALaT/IRPA (Royal Institute of Artistic Heritage), Belgica/KBR (Royal Library), Europeana/KULeuven (Katholieke Universiteit Leuven), and Wikimedia Commons.

    The questions can be in any language, but French and Dutch give the best results. If you don't get a correct answer, try rephrasing the question. The \
    assistant takes about 30 seconds to respond. He has a memory of the questions and answers session. The questions you ask may therefore \
    refer to previous questions and answers. For example: *Who painted that canvas?*
    """)

    st.markdown("""
    
    ### Concernant cet assistant
    
    Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge. Pour répondre, l'assistant \
    questionne différentes bases de données d'images comme BALaT/IRPA (Institut royal du Patrimoine artistique), Belgica/KBR (Bibliothèque royale), Europeana/KULeuven (Katholieke Universiteit Leuven) et Wikimedia Commons.

    Les questions peuvent-être posées en diférentes langues, mais le français et le néerlandais donnent les meilleurs résultats. Si vous n'obtenez pas une réponse \
    correcte, essayez de reformuler la question. L'assistant prend environ 30 secondes pour répondre. Il possède une mémoire de la session de questions et réponses. \
    Les questions que vous posez peuvent donc faire référence aux questions et réponses précédentes. Par exemple : *Qui a peint ce tableau ?*
    """)

    st.markdown("""
    _________
    AI Model: OpenAI GPT4 Turbo. Vector size: 3072. Hybrid RAG with memory powered by Langchain. Web interface powered by Streamlit. *(c) Eric Dodémont, 2024.*
    """)

# Initialize chat history (chat_history) for LangChain
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)   # Max k Q/A in the chat history for Langchain 

# Initialize chat history (messages) for Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model" not in st.session_state:
    st.session_state.model = "OpenAI: gpt-4-turbo-2024-04-09"

with st.chat_message("assistant"):
    st.write("Hello! Bonjour! Hallo! 👋")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if question := st.chat_input("Enter your question / Entrez votre question / Voer uw vraag in"):
    # Display user message in chat message container
    st.chat_message("user").markdown(question)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": question})

    output = ai_assistant_chain.invoke({"input": question, "chat_history": st.session_state.chat_history}) # output is a dictionary. output["answer"] is the LLM answer in markdown format.
    
    st.session_state.chat_history2.save_context({"input": question}, {"output": output["answer"]})
    load_memory = st.session_state.chat_history2.load_memory_variables({})
    st.session_state.chat_history = load_memory["history"]
        
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(output["answer"])
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": output["answer"]})

# $ streamlit run assistant.py &
# $ sudo streamlit run assistant.py --server.port 80 > assistant.log 2>&1 &
