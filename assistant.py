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

st.title('Belgian Monarchy Artworks Explorer - AI Assistant')

user_query = st.text_area("Enter your query: ", help='Type your query here and press enter.')

if st.button('Search'):
    if user_query:
        response = ai_assistant_chain.invoke(user_query)
        st.write(response)
    else:
        st.write("Please enter a query to proceed.")

#streamlit run assistant.py &
