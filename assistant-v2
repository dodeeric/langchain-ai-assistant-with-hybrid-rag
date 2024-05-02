# With chat history

import dotenv, jq
import streamlit as st
from PIL import Image
from langchain import hub
from langchain_community.document_loaders import JSONLoader
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
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large") # 3072 dimensions vectors used to embed the JSON items and the questions
vector_db = Chroma(embedding_function=embedding_model, collection_name=collection_name, persist_directory="./chromadb")

# Retrieve and generate

llm = ChatOpenAI(model="gpt-4-turbo-2024-04-09", temperature=0)

vector_retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

keyword_retriever = BM25Retriever.from_documents(documents)
keyword_retriever.k = 3

ensemble_retriever = EnsembleRetriever(retrievers=[keyword_retriever, vector_retriever], weights=[0.5, 0.5])

"""
# Without chat history:

prompt = hub.pull("dodeeric/rag-prompt-bmae")

def format_docs_clear_text(docs):
    return "\n\n".join(doc.page_content.encode('utf-8').decode('unicode_escape') for doc in docs)

ai_assistant_chain = (
    {"context": ensemble_retriever | format_docs_clear_text, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
"""

# With chat history:

chat_history = []

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

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

qa_system_prompt = """You are an artwork specialist. You must assist the users in finding, describing, and displaying artworks related to the Belgian monarchy. \
You first have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge Base", then answer with your own knowledge. \
You have to answer in the same language as the question.\n
At the end of the answer:\n
- give a link to a web page about the artwork (see the "url" field).\n
- display an image of the artwork (see the "og:image" field).\n
Knowledge Base:\n
\n
{context}"""

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
ai_assistant_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# Streamlit

logo = Image.open("./crown.jpg")
st.image(logo, use_column_width=True)

st.markdown("## Belgian Monarchy Artworks Explorer")

st.markdown("Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge.")
st.markdown("Pour répondre, l'assistant questionne les bases de données graphiques BALaT de l'IRPA (Institut royal du Patrimoine artistique), Belgica de la KBR (Bibliothèque royale) et Wikimedia Commons.")
st.markdown("Voici quelques exemples de questions : (elles peuvent-être en français, en néérlandais ou en anglais)")
st.markdown("- Pouvez-vous me montrer un tableau de Jan Verhas ?")
st.markdown("- Pouvez-vous me montrer un tableau de Jan Verhas provenant de la base de données BALaT, pas de la Wikimedia Commons ?")
st.markdown("- Qui est présent sur le tableau 'la revue des écoles' ?")
st.markdown("- Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?")
st.markdown("- Pouvez-vous me montrer un portrait du roi Léopol Ier ? Il faut que ce soit une gravure.")
st.markdown("- Pouvez-vous me montrer plusieurs images du roi Léopold II ?")
st.markdown("- Pouvez-vous me montrer des images du roi Léopold II lors de son avènement en 1865 ?")
st.markdown("- Avez-vous des oeuvres réalisées par Aimable Dutrieux ?")
st.markdown("- Pouvez-vous me montrer deux images de la fête patriotique du cinquantenaire de la Belgique réalisées par Martin Claverie ? Qui est présent sur ces images ? De quel journal proviennent-elles ?")
st.markdown("Si vous n'obtenez pas une réponse correcte, essayez de reformuler la question. Par exemple la question suivante ne reçois pas de réponse correcte : *Avez-vous un buste de Louis-Philipe, fils du roi Léopold Ier ?*, mais la question suivante reçoit elle une réponse correcte : *Avez-vous un buste de Louis-Philipe ?*")
st.markdown("L'assistant prend environ 30 secondes pour répondre.")
st.markdown("Pour l'instant, l'assistant ne possède pas de mémoire de la session de questions et réponses. Les questions que vous posez ne peuvent donc pas faire référence aux questions et réponses précédentes.")
st.markdown(" ")
st.markdown(" ")

question = st.text_area("Entrez votre question : ", help='Type your question here and press Control-Enter.')

if st.button('Répondre'):
    if question:
        #answer = ai_assistant_chain.invoke(question) # Without chat history
        output = ai_assistant_chain.invoke({"input": question, "chat_history": chat_history}) # output is a dictionary. output["answer"] is in markdown format.
        #st.markdown(answer) # Without chat history
        st.markdown(output["answer"]) # Showing the answer
        chat_history.extend([HumanMessage(content=question), output["answer"]]) # Adding the question and answer in the chat history
    else:
        st.write("Please enter a question to proceed.")

st.markdown(" ")
st.markdown(" ")
st.markdown("Modèle IA : GPT4 Turbo de OpenAI. Taille des vecteurs : 3072.")

st.markdown("*(c) Eric Dodémont, 2024.*")

#streamlit run assistant-v2.py &
