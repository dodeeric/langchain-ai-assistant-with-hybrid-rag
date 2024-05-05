# v31: with PDF indexation, with functions

import dotenv, jq, time
import streamlit as st
from PIL import Image
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain.chains import create_history_aware_retriever # To create the retriever chain (predefined chain)
from langchain.chains import create_retrieval_chain # To create the main chain (predefined chain)
from langchain.chains.combine_documents import create_stuff_documents_chain # To create a predefined chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

dotenv.load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-large"
MODEL = "gpt-4-turbo-2024-04-09"
COLLECTION_NAME = "bmae"

@st.cache_data
def load_files(json_file_paths, pdf_file_paths):
    # Loads and chunks files into a list of documents

    documents = []

    st.markdown("v31 -- documents: loading json...")
    time.sleep(10)

    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()
        documents = documents + docs

    st.markdown("v31 -- documents: loading pdf...")
    time.sleep(10)

    for pdf_file_path in pdf_file_paths:
        loader = PyPDFLoader(pdf_file_path)
        pages = loader.load_and_split() # 1 pdf page per chunk
        documents = documents + pages
    
    return documents

@st.cache_resource
def instanciate_vector_db():
    # Instantiates Vector DB and loads documents from disk
    
    st.markdown("v31 -- vector_db: loading...")
    time.sleep(10)

    collection_name = COLLECTION_NAME
    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL) # 3072 dimensions vectors used to embed the JSON items and the questions
    vector_db = Chroma(embedding_function=embedding_model, collection_name=collection_name, persist_directory="./chromadb")
        
    return vector_db

@st.cache_data
def instanciate_retrievers_and_chains(_documents, _vector_db):
    # Instantiate retrievers and chains and return the main chain (AI Assistant)
    # Retrieve and generate

    llm = ChatOpenAI(model=MODEL, temperature=0)

    vector_retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    keyword_retriever = BM25Retriever.from_documents(documents)
    keyword_retriever.k = 3

    ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vector_retriever], weights=[0.5, 0.5])

    contextualize_q_system_prompt = """
    Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
    """

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
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
    - give a link to a web page about the artwork (see the "url" field).
    - display an image of the artwork (see the "og:image" field).

    Knowledge Base:

    {context}
    """

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    st.markdown("v3 -- creating ai_assistant_chain...")
    time.sleep(10)

    ai_assistant_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return ai_assistant_chain

json_file_path1 = "./commons-urls-ds1-swp.json"
json_file_path2 = "./balat-ds1c-wcc-cheerio-ex_2024-04-06_09-05-15-262.json"
json_file_path3 = "./belgica-ds1c-wcc-cheerio-ex_2024-04-06_08-30-26-786.json"
json_file_path4 = "./commons-urls-ds2-swp.json"
json_file_path5 = "./balat-urls-ds2-swp.json"
json_file_paths = [json_file_path1, json_file_path2, json_file_path3, json_file_path4, json_file_path5]

pdf_file_path1 = "./BPEB31_DOS4_42-55_FR_LR.pdf"
pdf_file_paths = [pdf_file_path1]

documents = load_files(json_file_paths, pdf_file_paths)
vector_db = instanciate_vector_db()
ai_assistant_chain = instanciate_retrievers_and_chains(documents, vector_db)

# Streamlit

logo = Image.open("./crown.jpg")
st.image(logo, use_column_width=True)
st.markdown("""
## Belgian Monarchy Artworks Explorer

Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge. Pour répondre, l'assistant \
questionne les bases de données graphiques BALaT de l'IRPA (Institut royal du Patrimoine artistique), Belgica de la KBR (Bibliothèque royale) et Wikimedia Commons.

Les questions peuvent-être en français, en néerlandais ou en anglais, ou même en d'autres langues. En voici quelques exemples : 

- Quand est mort le roi Léopold Ier ? Avez-vous des images des funérailles ?
- Avez-vous des images de la reine Elisabeth pendant la guerre ?
- Pouvez-vous me montrer le tableau 'La revue des écoles' ? *Et ensuite vous pouvez poser la question :* 
- Qui a peint ce tableau ? *Et encore ensuite :* 
- Quelle est la dimension du tableau ?
- Qui est présent sur le tableau 'la revue des écoles' ? *Et ensuite vous pouvez poser la question :* 
- Pouvez-vous me montrer ce tableau avec une photo de la Wikimedia Commons et une autre photo de BALaT ?
- Quand a eu lieu l'incendie du château de Laeken ? Avez-vous plusieurs images de cet événement ?
- Quand s'est marié le roi Léopold Ier ? *L'assistant vous montrera une image du mariage.*
- Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?
- Pouvez-vous me montrer un portrait du roi Léopol Ier ? Il faut que ce soit une gravure.
- Pouvez-vous me montrer plusieurs images du roi Léopold II ?
- Pouvez-vous me montrer des images du roi Léopold II lors de son avènement en 1865 ?
- Avez-vous des oeuvres réalisées par Aimable Dutrieux ? *Et ensuite vous pouvez poser la question :*
- Qui était ce sculteur ?
- Pouvez-vous me montrer deux images de la fête patriotique du cinquantenaire de la Belgique réalisées par Martin Claverie ? Qui est présent sur ces images ? De quel journal proviennent-elles ?

Si vous n'obtenez pas une réponse correcte, essayez de reformuler la question. Par exemple la question suivante ne reçois pas de réponse correcte : *Avez-vous un buste de Louis-Philipe, fils du \
roi Léopold Ier ?*, mais la question suivante reçoit elle une réponse correcte : *Avez-vous un buste de Louis-Philipe ?*

L'assistant prend environ 30 secondes pour répondre.

L'assistant possède une mémoire de la session de questions et réponses. Les questions que vous posez peuvent donc faire référence aux questions et réponses précédentes. Par exemple : *Qui a peint ce tableau ?*
""")

if 'chat_history' not in st.session_state: # Mandatory
    st.session_state.chat_history = []

if 'question' not in st.session_state: # Not mandatory
    st.session_state.question = ""

if 'output' not in st.session_state: # Not mandatory
    st.session_state.output = None

st.session_state.question = st.text_area("Entrez votre question :", help='Type your question here and press Control-Enter.')

if st.button('Répondre'):
    if st.session_state.question:

        st.markdown("v31 -- calling ai_assistant_chain...")
        time.sleep(5)

        st.session_state.output = ai_assistant_chain.invoke({"input": st.session_state.question, "chat_history": st.session_state.chat_history}) # output is a dictionary. output["answer"] is the LLM answer in markdown format.
        st.markdown(st.session_state.output["answer"])
        time.sleep(5) # Wait for the chain/runnable to finish completely before updating the chat history, or else the chat history is not correct in the Langsmith logs 
        st.session_state.chat_history.extend([HumanMessage(content=st.session_state.question), st.session_state.output["answer"]]) # Adding the question and answer in the chat history
    else:
        st.write("Please enter a question to proceed.")

st.markdown("""
AI Model: OpenAI GPT4 Turbo. Vector size: 3072. Hybrid RAG with memory powered by LangChain. Web interface powered by Streamlit. *(c) Eric Dodémont, 2024.*
""")

#streamlit run assistant-vX.py > bmae.log 2>&1 &
