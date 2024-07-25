# RagAiAgent: Langchain/Langraph AI Agent with Hybrid RAG

This application can be configured (see config.py) to create your own specialized AI agent.

## Features

- AI Python framework: Langchain and Langgraph
- Web interface Python framework: Streamlit
- Vector DB: Chroma (can run locally or on a remote server)
- Tool n° 1: Hybrid RAG: bm25 keyword search and vector db semantic search (BM25Retriever + vector_db.as_retriever = EnsembleRetriever). Hybrid RAG improves greatly the efficiency of the RAG search.
- Tool n° 2: Web search
- Chat history
- Logs sent to Langsmith
- AI Models: OpenAI GPT 4o, Google Gemini 1.5, Anthropic Claude 3.5, Ollama (Llama 3, etc.). Vector size: 3072.
- Admin interface: scrape web pages, upload PDF files, embed in vector DB, change model, etc.
- Files ingestion into the vector DB: JSON files (one JSON item / web page per chunk) and PDF files (one PDF page per chunk)
- Fully customisable with parameters in the config.py configuration file.
- Multilanguage RAG (knowlege base with data in different languages).
 
## Frameworks and tools

- Langchain & Langraph: https://www.langchain.com (Python framework for AI applications)
- Langsmith: https://smith.langchain.com (logs and debug for Langchain applications)
- Streamlit: https://streamlit.io (Python framework for web interfaces for data / AI applications)
- Chroma: https://www.trychroma.com (Vector DB)
- Chromadb Admin: https://github.com/flanker/chromadb-admin (Web admin interface for Chroma)
- OpenAI (GPT): https://platform.openai.com (LLM)
- Anthropic (Claude): https://console.anthropic.com/dashboard (LLM)
- Google (Gemini): https://aistudio.google.com/app (LLM)
- Google VertexAI (Gemini): https://cloud.google.com/vertex-ai (LLM)
- Ollama (Llama, etc.): https://ollama.com (LLM)
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup (Web scraping)
- Tavily: https://tavily.com (Web search for LLM)

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
GOOGLE_API_KEY = "xxx"               ==> Go to https://aistudio.google.com/app/apikey
LANGCHAIN_API_KEY = "ls__xxx"        ==> Go to https://smith.langchain.com (Langsmith)
LANGCHAIN_TRACING_V2 = "true"        ==> Set to false if you will not use Langsmith traces
ADMIN_PASSWORD = "xxx"               ==> You chose your password
GOOGLE_APPLICATION_CREDENTIALS = "./serviceaccountxxx.json"  ==> Path to the Service Account (with VertexAI role) JSON file
CHROMA_SERVER_AUTHN_CREDENTIALS ="xxx"   ==> You chose the password for the Chroma DB authentication
CHROMA_SERVER_AUTHN_PROVIDER="chromadb.auth.token_authn.TokenAuthenticationServerProvider"
TAVILY_API_KEY = "tvly-xxx"          ==> Go to https://app.tavily.com/home
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

- Configure the "Chroma connection string": Ex.: http://myvm2.edocloud.be:8000
- Set "Authentication Type" to "Token", and introduce the Chroma token/password as configured in the environment variable.

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

With the Azure Web interface (Console), or with a Bicep or JSON ARM template, or with a Terraform configuration, or with the Azure CLI or Azure Powershell CLI, create:

* An App service plan
* A Web App with: Continuous deployment = Disabled

Example of Bicep ARM template and Azure DevOps pipeline:

File: web-app.bicep

```
module appServicePlan 'br/public:avm/res/web/serverfarm:0.2.0' = {
  name: 'appServicePlanDeployment'
  params: {
    name: 'ragai-appserviceplan'
    skuCapacity: 1
    skuName: 'B1'   // Standard S is deprecated
    kind: 'Linux'
    reserved: true   // Mandatory if Linux
  }
}

module webApp 'br/public:avm/res/web/site:0.3.8'  = {
  name: 'webAppDeployment'
  params: {
    kind: 'app,linux'
    name: 'ragai-webapp'
    serverFarmResourceId: appServicePlan.outputs.resourceId
    location: 'westeurope'
    siteConfig: {
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
      ]
      linuxFxVersion: 'PYTHON|3.10'
    }
  }
}
```

File: azure-pipeline.yml

```
name: $(Build.DefinitionName)_$(SourceBranchName)_$(Date:yyyyMMdd).$(Rev:r)

variables:
  - group: environment-variables

parameters:
  - name: location
    displayName: The location of the resource group
    type: string
    default: 'westeurope'
  - name: resourcegroup
    displayName: The name of the resource group (rg)
    type: string
    default: 'ragai-rg'

trigger: none
    
stages:
  - stage: Stage_1
    displayName: 'Stage 1: Deploy resource group'
    jobs:
    - job: Job_1
      displayName: 'Deploy Job 1'
      steps:
        - task: AzureCLI@2
          displayName: 'Deploy Step 1'
          inputs:
            azureSubscription: $(subscription)
            scriptType: bash
            scriptLocation: inlineScript
            inlineScript: |
              echo "Creating resource group..."
              az group create --name ${{parameters.resourcegroup}} --location ${{parameters.location}}
              
  - stage: Stage_2
    displayName: 'Stage 2: Deploy web app'
    jobs:
    - job: Job_1
      displayName: 'Deploy Job 1'
      steps:
        - task: AzureCLI@2
          displayName: 'Deploy Step 1'
          inputs:
            azureSubscription: $(subscription)
            scriptType: bash
            scriptLocation: inlineScript
            inlineScript: |
              echo "Deploy web app..."
              az deployment group create --resource-group ${{parameters.resourcegroup}} --template-file './azure-web-app/web-app.bicep'
```           

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
* Introduce one by one ("Add", then "Apply", "Confirm") the environment variables (see above).

3. Restart the Web App (it takes some time for the app to become up and running). To see Application logs, go to: Web App > Diagnose and solve problems > Availability and Performance > Application Logs > Platform logs.

Demo: https://bmae-ragai-webapp.azurewebsites.net (running the app only, not the db)

## Install blobfuse2 (OPTIONAL)

Procedure to mount an Azure Blob container on the local filesystem 'files' directory

Example for Linux Ubuntu 22.04.4 LTS (Jammy)

### Install blobfuse2

```
sudo wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install libfuse3-dev fuse3 blobfuse2
```

### Configure blobfuse2

```
mkdir blobfusetmp
mkdir files
```
```
nano blobfuse.yaml
```
``` 
logging:
  type: syslog
  level: log_debug

components:
  - libfuse
  - file_cache
  - attr_cache
  - azstorage

libfuse:
  attribute-expiration-sec: 120
  entry-expiration-sec: 120
  negative-entry-expiration-sec: 240

file_cache:
  path: blobfusetmp
  timeout-sec: 120
  max-size-mb: 4096

attr_cache:
  timeout-sec: 7200

azstorage:
  type: block
  account-name: bmaeragaisa
  account-key: xxx
  endpoint: https://bmaeragaisa.blob.core.windows.net
  mode: key
  container: bmae-ragai-blobcontainer
```
```
chmod 600 blobfuse.cfg
```

The parameters you have to adapt are:

- The cache directory: path: blobfusetmp
- The Azure storage account name: account-name: bmaeragaisa
- The Azure storage account access key: account-key: xxx
- The Azure storage account URL: https://bmaeragaisa.blob.core.windows.net
- The Azure blob container name: bmae-ragai-blobcontainer

### Mount the blob container on the local FS

To mount the blob container on the 'files' directory:

```
blobfuse2 mount ./files --config-file=./blobfuse.yaml
```
or
```
bash fuse<sh
```

### Logs

Logs are available in two files: /var/log/blobfuse*.log

### Checks

```
df -a
blobfuse2 mount list
```

### Web sites

How to mount an Azure Blob Storage container on Linux with BlobFuse2: https://learn.microsoft.com/en-us/azure/storage/blobs/blobfuse2-how-to-deploy?tabs=Ubuntu

Blobfuse2 Installation: https://github.com/Azure/azure-storage-fuse/wiki/Blobfuse2-Installation

## Local (filesystem) or remote (server)

### Chroma DB:

config.py:

- Local: server = False
- Server: server = True

### Files (JSON and PDF)

Directory: files

- Local: nothing to configure
- Server: mount Azure Blob container on the local FS via Blobfuse2 (blobfuse.sh)
