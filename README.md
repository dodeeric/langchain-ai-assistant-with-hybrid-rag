# Langchain AI Assistant with Hybrid RAG and Memory

AI assistant with:
- hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever)
- chat history (predefined chains: history_aware_retriever, stuff_documents_chain, retrieval_chain)
- vector DB: Chroma
- web interface: Streamlit

Available at http://bmae.edocloud.be:8501
