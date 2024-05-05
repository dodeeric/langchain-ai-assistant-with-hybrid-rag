# LangChain AI Assistant with Hybrid RAG and Memory

AI assistant with:
- hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever) (this improve greatly the efficiency of the RAG search)
- chat history (predefined chains: history_aware_retriever, stuff_documents_chain, retrieval_chain)
- vector DB: Chroma
- web interface: Streamlit
- files ingestion into the RAG (vector DB): JSON files (one JSON item per chunk) and PDF files (one PDF page per chunk)

Available at http://bmae.edocloud.be:8501

Installation:

$ git clone https://github.com/dodeeric/langchain-ai-assistant-with-hybrid-rag.git
$ cd langchain-ai-assistant-with-hybrid-rag

Install required libraries:

"""
$ pip install -r requirements.txt
"""

Embedd JSON items and PDF pages:

$ python embbed.py

Check the Chroma vector DB: (OPTIONAL)

$ cd chromadb
$ sqlite3 chroma.sqlite3
sqlite> .tables ===> List of the tables
sqlite> select * from collections; ===> Name of the collection (bmae) & size of the vectors (3072)
sqlite> select count(*) from embeddings; ===> Number of records in the db
sqlite> select id, key, string_value from embedding_metadata LIMIT 10 OFFSET 0; ===> Display JSON items and PDF pages

Launch the AI Assistant:

$ streamlit run assistant.py &

Go to: http://IP:8501
