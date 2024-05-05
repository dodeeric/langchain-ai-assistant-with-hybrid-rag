# LangChain AI Assistant with Hybrid RAG and Memory

AI assistant coded with the LangChain framework:
- hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever) (this improve greatly the efficiency of the RAG search)
- chat history (predefined chains: history_aware_retriever, stuff_documents_chain, retrieval_chain)
- vector DB: Chroma
- web interface: Streamlit
- files ingestion into the RAG (vector DB): JSON files (one JSON item per chunk) and PDF files (one PDF page per chunk)
- logs sent to LangSmith
 
Frameworks and tools:

- LangChain: https://www.langchain.com (Python framework for AI applications)
- LangSmith: https://smith.langchain.com (logs and debug for LangChain applications)
- Streamlit: https://streamlit.io (web interface Python framework for data / AI applications)
- Chroma: https://www.trychroma.com (Vector DB)
- OpenAI: https://platform.openai.com (LLMs)

Available at http://bmae.edocloud.be:8501

This code can be adapted to create your own AI assistant.

Installation:

```
$ git clone https://github.com/dodeeric/langchain-ai-assistant-with-hybrid-rag.git
$ cd langchain-ai-assistant-with-hybrid-rag
```

Add your API keys:

```
$ nano .env
```

```
OPENAI_API_KEY = "sk-xxx"   ==> Go to: https://platform.openai.com/api-keys
LANGCHAIN_API_KEY = "ls__xxx"   ==> go to: https://smith.langchain.com/
LANGCHAIN_TRACING_V2 = "true"
```

Install required libraries:

```
$ pip install -r requirements.txt
```

Embedd JSON items and PDF pages:

```
$ python embbed.py
```

Check the Chroma vector DB: (OPTIONAL)

```
$ cd chromadb
$ sqlite3 chroma.sqlite3
```
```
sqlite> .tables ===> List of the tables
sqlite> select * from collections; ===> Name of the collection (bmae) & size of the vectors (3072)
sqlite> select count(*) from embeddings; ===> Number of records in the db
sqlite> select id, key, string_value from embedding_metadata LIMIT 10 OFFSET 0; ===> Display JSON items and PDF pages
```

Launch the AI Assistant:

```
$ streamlit run assistant.py &
```

Go to: http://IP:8501

At the Begining of the Jupyter notebook: see code to scrap web pages content given a list of URLs.
