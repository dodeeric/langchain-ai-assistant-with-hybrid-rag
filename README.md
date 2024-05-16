# LangChain AI Assistant with Hybrid RAG and Memory

This code can be adapted to create your own AI assistant.

AI assistant coded with the LangChain framework:

- Hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever) (this improve greatly the efficiency of the RAG search)
- Chat history (predefined chains: history_aware_retriever, stuff_documents_chain, retrieval_chain)
- Vector DB: Chroma
- Web interface: Streamlit
- Files ingestion into the RAG (vector DB): JSON files (one JSON item per chunk) and PDF files (one PDF page per chunk)
- Logs sent to LangSmith
- AI Model: OpenAI, Google, Anthropic, Ollama (Llama3, etc.). Vector size: 3072.

At the begining of the Jupyter notebook: see code to scrap web pages content given a list of URLs and the CSS class to scrap. Is added in the JSON item: the page url (url field), the page metadata (opengraph from Facebook) (metadata field), the text of the page (text field). For Wikimedia Commons, you can crowl and scrape the pages of a category.
 
Frameworks and tools:

- LangChain: https://www.langchain.com (Python framework for AI applications)
- LangSmith: https://smith.langchain.com (logs and debug for LangChain applications)
- Streamlit: https://streamlit.io (web interface Python framework for data / AI applications)
- Chroma: https://www.trychroma.com (Vector DB)
- OpenAI: https://platform.openai.com (LLMs)

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
OPENAI_API_KEY = "sk-xxx"       ==> Go to: https://platform.openai.com/api-keys
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
sqlite> .tables                            ===> List of the tables
sqlite> select * from collections;         ===> Name of the collection (bmae) & size of the vectors (3072)
sqlite> select count(*) from embeddings;   ===> Number of records in the DB
sqlite> select id, key, string_value from embedding_metadata LIMIT 10 OFFSET 0;       ===> Display JSON items and PDF pages
sqlite> PRAGMA table_info(embedding_metadata);                                        ===> Structure of the table   
sqlite> select * from embedding_metadata where string_value like '%Delper%';          ===> Display matching records
sqlite> select count(*) from embedding_metadata where string_value like '%Delper%';   ===> Display number of matching records
```

Launch the AI Assistant:

```
$ streamlit run assistant.py &
```

Go to: http://IP:8501

---

Available at http://bmae.edocloud.be

This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art and the Belgian monarchy. To answer, the assistant queries the graphic databases BALaT of the IRPA (Royal Institute of Artistic Heritage), Belgica of the KBR (Royal Library) and Wikimedia Commons.

![bmae](./screenshot.jpg)

---

Running with Ollama / Llama 3 in place of OpenAI GPT4 Turbo:

Install Ollama

$ ollama pull llama3
$ ollama list
$ ollama serve

New window:

$ ollama run llama3
>>> What's the capital of France?
>>> /bye
