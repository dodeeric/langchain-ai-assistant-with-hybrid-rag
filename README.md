# Langchain AI Assistant with Hybrid RAG and Memory (ragai)

This application can be configured (see config.py) to create your own specialized AI assistant.

## Features

- AI Python framework: Langchain
- Web interface Python framework: Streamlit
- Vector DB: Chroma (can run locally or on a remote server)
- Hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever). Hybrid RAG improves greatly the efficiency of the RAG search.
- Chat history with limited size (use of predefined chains: history_aware_retriever, stuff_documents_chain, retrieval_chain)
- Streaming of the AI answer
- Logs sent to Langsmith
- AI Models: OpenAI GPT 4o, Google Gemini 1.5, Anthropic Claude 3, Ollama (Llama 3, etc.). Vector size: 3072.
- Admin interface (scrape web pages, upload PDF files, embed in vector DB, change model, etc.)
- Files ingestion into the vector DB: JSON files (one JSON item / web page per chunk) and PDF files (one PDF page per chunk)
- Fully customisable with parameters in the config.py configuration file.
 
## Frameworks and tools

- Langchain: https://www.langchain.com (Python framework for AI applications)
- Langsmith: https://smith.langchain.com (logs and debug for Langchain applications)
- Streamlit: https://streamlit.io (Python framework for web interfaces for data / AI applications)
- Chroma: https://www.trychroma.com (Vector DB)
- Chromadb Admin: https://github.com/flanker/chromadb-admin (Web admin interface for Chroma)
- OpenAI (GPT): https://platform.openai.com (LLM)
- Anthropic (Claude): https://console.anthropic.com/dashboard (LLM)
- Google VertexAI (Gemini): https://cloud.google.com/vertex-ai (LLM)
- Ollama (Llama, etc.): https://ollama.com (LLM)

## Procedure to install the application on a Linux server

Demo: https://bmae.edocloud.be (running the app, the db, and a reverse proxy on an Azure virtual machine)

Requirements: Python 3.10+

```
$ git clone https://github.com/dodeeric/langchain-ai-assistant-with-hybrid-rag.git
$ cd langchain-ai-assistant-with-hybrid-rag
```

Add your API keys (only the OpenAI API key is mandatory) and admin password:

```
$ nano .env
```

```
OPENAI_API_KEY = "sk-proj-xxx"       ==> Go to https://platform.openai.com/api-keys
ANTHROPIC_API_KEY = "sk-ant-xxx"     ==> Go to https://console.anthropic.com/settings/keys
LANGCHAIN_API_KEY = "ls__xxx"        ==> Go to https://smith.langchain.com (Langsmith)
LANGCHAIN_TRACING_V2 = "true"        ==> Set to false if you will not use Langsmith traces
ADMIN_PASSWORD = "xxx"               ==> You chose your password
GOOGLE_APPLICATION_CREDENTIALS = "./serviceaccountxxx.json"  ==> Path to the Service Account (with VertexAI role) JSON file
```

Configure the application:

```
$ nano config/config.py
```

Install required libraries:

```
$ pip install -U -r requirements.txt
```

Launch the Chroma DB server: (on the same server as the app or another one)

```
$ bash db.sh start
```

Launch the AI Assistant:

```
$ bash app.sh start
```

Remark: if you get the "streamlit: command not found" error, then log off, then log in, to have the PATH updated.

Go to: http://IP:8080 (the IP is displayed on the screen in the "External URL".)

Go first to the admin interface (introduce the admin password), and scrape some web pages and/or upload some PDF files, then embed them to the vector DB.

### Install and configure Nginx as reverse proxy (OPTIONAL)

For example:

* Internal/private IP and port: 10.0.0.4:8080
* External/public IP and port: 172.205.226.216:80 (domain name: bmae.edocloud.be)

```
$ sudo apt update
$ sudo apt install nginx
$ sudo nano /etc/nginx/sites-available/streamlitnginxconf
```
```
server {
  listen 80;
  server_name bmae.edocloud.be www.bmae.edocloud.be;
  location / {
    proxy_pass http://10.0.0.4:8080;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;
    proxy_redirect off;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```
```
$ sudo ln -s /etc/nginx/sites-available/streamlitnginxconf /etc/nginx/sites-enabled/streamlitnginxconf
$ sudo systemctl restart nginx
```

Go to: http://172.205.226.216 or http://bmae.edocloud.be

More info: https://ngbala6.medium.com/deploy-streamlit-app-on-nginx-cfa327106050

### Configure a TLS certificate for https (port 443) (OPTIONAL)

```
$ sudo snap install --classic certbot
$ sudo ln -s /snap/bin/certbot /usr/bin/certbot
$ sudo certbot --nginx -d bmae.edocloud.be -d www.bmae.edocloud.be
$ sudo certbot renew --dry-run
```

Go to: https://172.205.226.216 or https://bmae.edocloud.be

More info: https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-18-04

### Check the Chroma vector DB (OPTIONAL)

From the server on which Chroma is installed:

```
$ sudo apt install sqlite3
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
sqlite> .quit
```

### Install a web interface for the Chroma vector DB (Chromadb Admin) (OPTIONAL)

From the server on which Chroma is installed:

```
$ git clone https://github.com/flanker/chromadb-admin.git
$ cd chromadb-admin/
$ sudo docker build -t chromadb-admin .
$ sudo docker run -p 3000:3000 chromadb-admin &
```

Configure the "Chroma connection string": Ex.: http://myvm2.edocloud.be:8000

Demo: http://bmae.edocloud.be:3000

### Running Ollama / Llama 3 (or another LLM) locally (OPTIONAL)

Install Ollama:

```
$ curl -fsSL https://ollama.com/install.sh | sh
```

The Ollama API is now available at 127.0.0.1:11434.

Run the Llama 3 LLM:

```
$ ollama pull llama3
$ ollama list
$ ollama serve
```

Query the LLM in a new window:

```
$ ollama run llama3
>>> What's the capital of France?
>>> /bye
```

To make Ollama listen on all IPs, not only 127.0.0.1:

```
$ sudo nano /etc/systemd/system/ollama.service

[Services]
Environment="OLLAMA_HOST=0.0.0.0"

$ sudo systemctl daemon-reload
$ sudo systemctl restart ollama
$ sudo systemctl status ollama
```

## Procedure to install the application on Streamlit Community cloud

* [Streamlit Community cloud](https://streamlit.io/cloud)

You can deploy directly from Github repository to Streamlit Community cloud.

Demo: https://bmae-ai-assistant.streamlit.app (running the app)

## Procedure to install the application on Azure Web App service

* [Azure Web App service](https://azure.microsoft.com/en-us/products/app-service/web)
* [Continuous deployment to Azure Web App service](https://learn.microsoft.com/en-us/azure/app-service/deploy-continuous-deployment?tabs=github%2Cgithubactions)
* [How to deploy a Streamlit application to Azure Web App service](https://learn.microsoft.com/en-us/answers/questions/1470782/how-to-deploy-a-streamlit-application-on-azure-app)

You can deploy directly from Github repository to Azure Web App service with Github Actions workflow.

Procedure:

A) Create the App service plan and the App service (Web App)

Via the Azure Web interface (Console), create:

* An App service plan
* A Web App with: Continuous deployment = Disabled

B) Configure the deployment source

* In the Azure portal, go to the management page for your Web App.
* In the left pane, select "Deployment Center". Then select "Settings".
* In the "Source" box, select "GitHub".
* If you're deploying from GitHub for the first time, select "Authorize" and follow the authorization prompts.
* After you authorize your Azure account with GitHub, select the "Organization", "Repository", and "Branch" you want.
* Under "Authentication type", select "Basic authentication". Then click on the red message (SCM Basic Auth. is not allowed), and set: SCM Basic Auth. Publishing = On, and click on "Save", and "Continue". Then back to the previous page.
* Select "Save". New commits in the selected repository and branch now deploy continuously into your Web App. You can track the commits and deployments on the "Logs" tab.
* Wait for the deployment to finish (15 minutes or so). The Actions workflow YAML file is added in your repo in: .github/workflow/xxxx.yml. Go to Github > Actions, and click on the workflow run to see the Build and Deploy.

C) Configure the "Startup Command"

* Go to "Web App" > "Configuration".
* In "Startup Command", add: 

```
python -m streamlit run Assistant.py --server.port 8000 --server.address 0.0.0.0
```

And click on "Save", then "Continue".

* Go to the URL of the Web App, you should see the application running, but with errors. If needed, restart the Web App (it takes some time for the app to become up and running).

D) Add the "Environment variables"

* Go to "Web App" > "Environment variables".
* Introduce one by one ("Add", then "Apply", "Confirm"):

```
OPENAI_API_KEY = "sk-proj-xxx"       ==> Go to https://platform.openai.com/api-keys
ANTHROPIC_API_KEY = "sk-ant-xxx"     ==> Go to https://console.anthropic.com/settings/keys
LANGCHAIN_API_KEY = "ls__xxx"        ==> Go to https://smith.langchain.com (Langsmith)
LANGCHAIN_TRACING_V2 = "true"        ==> Set to false if you will not use Langsmith traces
ADMIN_PASSWORD = "xxx"               ==> You chose your password
GOOGLE_APPLICATION_CREDENTIALS = "./serviceaccountxxx.json"  ==> Path to the Service Account (with VertexAI role) JSON file
```

3. Restart the Web App (it takes some time for the app to become up and running). To see Application logs, go to: Web App > Availability and Performance > Application Logs > Platform logs.

Demo: https://bmae-ragai-webapp.azurewebsites.net (running the app only, not the db)
