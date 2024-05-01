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

dotenv.load_dotenv()

# Index

file_path1 = "./commons-urls-ds1-swp.json"
file_path2 = "./balat-ds1c-wcc-cheerio-ex_2024-04-06_09-05-15-262.json"
file_path3 = "./belgica-ds1c-wcc-cheerio-ex_2024-04-06_08-30-26-786.json"
file_paths = [file_path1, file_path2, file_path3]

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

prompt = hub.pull("dodeeric/rag-prompt-bmae")

def format_docs_clear_text(docs):
    return "\n\n".join(doc.page_content.encode('utf-8').decode('unicode_escape') for doc in docs)

ai_assistant_chain = (
    {"context": ensemble_retriever | format_docs_clear_text, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Streamlit

logo = Image.open("./crown.jpg")
st.image(logo, use_column_width=True)

st.markdown("## Belgian Monarchy Artworks Explorer")

st.markdown("Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge.")
st.markdown("Pour répondre, l'assistant questionne les bases de données graphiques BALaT de l'IRPA (Institut royal du Patrimoine artistique), Belgica de la KBR (Bibliothèque royale), et Wikimedia Commons.")
st.markdown("Voici quelques exemples de questions :")
st.markdown("- Pouvez-vous me montrer un tableau de Jan Verhas ?")
st.markdown("- Pouvez-vous me montrer un tableau de Jan Verhas provenant de la base de données BALaT, pas de la Wikimedia Commons ?")
st.markdown("- Qui est présent sur le tableau 'la revue des écoles' ?")
st.markdown("- Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?")
st.markdown("- Pouvez-vous me montrer un portrait du roi Léopol Ier ? Il faut que ce soit une gravure.")
st.markdown("Si vous n'obtenez pas une réponse correcte, essayez de reformuler la question. Par exemple la question suivante ne reçois pas de réponse correcte : *Avez-vous un buste de Louis-Philipe, fils du roi Léopold Ier ?*, mais la question suivante reçoit elle une réponse correcte : *Avez-vous un buste de Louis-Philipe ?*.")
st.markdown("L'assistant prend environ 30 secondes pour répondre.")
st.markdown("Pour l'instant, l'assistant ne possède pas de mémoire de la session de questions et réponses. Les questions que vous posez ne peuvent donc pas faire référence aux questions et réponses précédentes.")
st.markdown(" ")
st.markdown(" ")

user_query = st.text_area("Entrez votre question : ", help='Type your question here and press Control-Enter.')

if st.button('Répondre'):
    if user_query:
        response = ai_assistant_chain.invoke(user_query)
        st.markdown(response)
    else:
        st.write("Please enter a query to proceed.")

st.markdown(" ")
st.markdown(" ")
st.markdown("Modèle IA : GPT4 Turbo de OpenAI. Taille des vecteurs : 3072.")

st.markdown("*(c) Eric Dodémont, 2024.*")

#streamlit run assistant.py &
