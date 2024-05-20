#!/usr/bin/env python

"""
This function runs the frontend web interface.
"""

# v2: stream output
# v3: integrate admin in main web interface
# v4: move model selection to admin interface + move files dir to json_files + add admin password

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from PIL import Image
from langchain.memory import ConversationBufferWindowMemory
from modules.assistant_backend_v1 import instanciate_ai_assistant_chain

import requests, json, shutil
from bs4 import BeautifulSoup
from modules.scrape_web_page_v1 import scrape_web_page
import streamlit as st
import os
from langchain_community.document_loaders import JSONLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


def scrape_commons_category(category):
    """
    METHOD 3: For Commons: Scrape the URLs from a Commons Category and save the results in a JSON file
    """
    
    FILE_PATH = "./json_files/commons-"

    #category = "Category:Prince_Philippe,_Count_of_Flanders_in_photographs"

    items = []
    href_old = ""

    # Step 1: Load the HTML content from a webpage
    url = f"https://commons.wikimedia.org/wiki/{category}"
    response = requests.get(url)
    html_content = response.text

    # Step 2: Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Find all URLs in  tags
    urls = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            if href.startswith("/wiki/File:") and href != href_old: # This test because all links are in double!
                urls.append(f"https://commons.wikimedia.org{href}")
                href_old = href

    number_of_pages = len(urls)
    st.write(f"Number of pages to scrape: {number_of_pages}")

    i = 1
    items = []
    for url in urls:
        st.write(f"Scraping {i}/{number_of_pages}...")
        url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
        item = scrape_web_page(url, "hproduct commons-file-information-table")
        print(item)
        items.append(item)
        #time.sleep(1)
        i = i + 1

    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"{FILE_PATH}{category}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()


def scrape_europeana_url(url):
    """
    METHOD 4: Scrape one URL (should be Europeana) and save the result in a JSON file
    """

    #url = "https://www.europeana.eu/en/item/0940429/_nhtSx4z"

    # Step 1: Load the HTML content from a webpage
    #response = requests.get(url)
    #html_content = response.text

    # Step 2: Parse the HTML content
    #soup = BeautifulSoup(html_content, 'html.parser')

    url = url.replace("\ufeff", "")  # Remove BOM (Byte order mark at the start of a text stream)
    item = scrape_web_page(url, "card metadata-box-card mb-3")
    print(item)
    items = []
    items.append(item)   # Add in a list, even if only one item

    url2 = url.replace("https://","")
    url2 = url2.replace("http://","")
    url2 = url2.replace("/","-")
    # Save the Python list in a JSON file
    # json.dump is designed to take the Python objects, not the already-JSONified string. Read docs.python.org/3/library/json.html.
    with open(f"./json_files/{url2}-swp.json", "w") as json_file:
        json.dump(items, json_file) # That step replaces the accentuated characters (ex: é) by its utf8 codes (ex: \u00e9)
    json_file.close()


def load_files_and_embed(json_file_paths, pdf_file_paths):
    """
    Loads and chunks files into a list of documents then embed
    """

    EMBEDDING_MODEL = "text-embedding-3-large"
    COLLECTION_NAME = "bmae"

    embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    nbr_files = len(json_file_paths)
    st.write(f"Embeding {nbr_files} JSON files...")
    documents = []
    for json_file_path in json_file_paths:
        loader = JSONLoader(file_path=json_file_path, jq_schema=".[]", text_content=False)
        docs = loader.load()   # 1 JSON item per chunk
        print(f"JSON file: {json_file_path}, Number of JSON items: {len(docs)}")
        documents = documents + docs
    st.write(f"Total number of JSON items: {len(documents)}")
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")

    nbr_files = len(pdf_file_paths)
    st.write(f"Embeding {nbr_files} PDF files...")
    documents = []
    if pdf_file_paths:  # if equals to "", then skip
        for pdf_file_path in pdf_file_paths:
            loader = PyPDFLoader(pdf_file_path)
            pages = loader.load_and_split()  # 1 pdf page per chunk
            print(f"PDF file: {pdf_file_path}, Number of PDF pages: {len(pages)}")
            documents = documents + pages
    st.write(f"Total number of PDF pages: {len(documents)}")
    Chroma.from_documents(documents, embedding_model, collection_name=COLLECTION_NAME, persist_directory="./chromadb")


def delete_directory(dir_path):
    try:
        shutil.rmtree(dir_path)
        print(f"Directory '{dir_path}' and all its contents have been deleted successfully")
    except FileNotFoundError:
        print(f"Error: Directory '{dir_path}' does not exist")
    except PermissionError:
        print(f"Error: Permission denied to delete '{dir_path}'")
    except Exception as e:
        print(f"Error: {e}")


def assistant_frontend():
    """
    All related to Streamlit and connection with the Langchain backend. Includes also the admin interface.
    """

    # Initialize chat history (chat_history) for LangChain
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)   # Max k Q/A in the chat history for Langchain

    # Initialize chat history (messages) for Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model" not in st.session_state:
        st.session_state.model = "OpenAI (2): gpt-4o-2024-05-13"

    # Load, index, retrieve and generate

    ai_assistant_chain = instanciate_ai_assistant_chain(st.session_state.model)

    # # # # # # # #
    # Main window #
    # # # # # # # #

    logo = Image.open("./images/image.jpg")
    st.image(logo, use_column_width=True)

    st.markdown("## Belgian Monarchy Artworks Explorer")
    st.caption("💬 A chatbot powered by Langchain and Streamlit")

    # # # # # # # # # #
    # Side bar window #
    # # # # # # # # # #

    with st.sidebar:

        #page = st.radio("Go to page:", ["About", "Admin"])

        # Two buttons in place of two radio buttons
        #col1, col2 = st.columns(2)
        #page = "About"
        #with col1:
        #    if st.button("About"):
        #        page = "About"
        #with col2:
        #    if st.button("Admin"):
        #        page = "Admin"

        password_ok = "no"
        password = "XXXX"
        page = "About"
        # Ask admin password to access admin menu
        admin_password = os.getenv("ADMIN_PASSWORD", "YYYY")
        password = st.text_input("Enter admin password: ", type="password")
        if password != admin_password:
            page = "About"
            password_ok = "no"
        else:
            page = "Admin"
            password_ok = "yes"

        # Side bar: first or second page
        if page == "About":
        
            # # # # # # # # # # # # # # # # # # # #
            # Side bar window: first page (About) #
            # # # # # # # # # # # # # # # # # # # #

            st.markdown("""
            ### About this assistant

            This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art and the Belgian monarchy. To answer, the assistant \
            queries different images databases like BALaT/IRPA (Royal Institute of Artistic Heritage), Belgica/KBR (Royal Library), Europeana/KULeuven (Katholieke Universiteit Leuven), and Wikimedia Commons.

            The questions can be in any language, but French and Dutch give the best results. If you don't get a correct answer, try rephrasing the question, or just ask the same question again. The \
            assistant takes about 30 seconds to respond. He has a memory of the questions and answers session. The questions you ask may therefore refer to previous questions and answers. For \
            example: *Who painted that canvas?*
            """)

            st.markdown("""

            ### Concernant cet assistant

            Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge. Pour répondre, l'assistant \
            questionne différentes bases de données d'images comme BALaT/IRPA (Institut royal du Patrimoine artistique), Belgica/KBR (Bibliothèque royale), Europeana/KULeuven (Katholieke Universiteit Leuven) et Wikimedia Commons.

            Les questions peuvent-être posées en différentes langues, mais le français et le néerlandais donnent les meilleurs résultats. Si vous n'obtenez pas une réponse \
            correcte, essayez de reformuler la question, ou reposez à nouveau la même question. L'assistant prend environ 30 secondes pour répondre. Il possède une mémoire de la session de questions et réponses. \
            Les questions que vous posez peuvent donc faire référence aux questions et réponses précédentes. Par exemple : *Qui a peint ce tableau ?*
            """)

            st.markdown("""

            #### Examples of questions you can ask

            ENGLISH:

            - When did King Leopold I die? Do you have any images of the funeral?
            - Do you have any images of Queen Elizabeth during the First World War?
            - Can you show me the canvas "The school review"? *And then you can ask the question:*
            - Who painted this canvas? *And then again:*
            - What is the size of the canvas? *And then again:*
            - Who is present on this canvas? *And then again:*
            - Can you show me this canvas with a photo from Wikimedia Commons and another photo from BALaT?
            - When did the fire at Laeken Castle take place? Do you have images of this event?
            - When did King Leopold I get married? *The assistant will show you an image of the wedding.*
            - Can you show me a portrait of King Leopold I? It has to be an engraving.
            - Can you show me images of King Leopold II?
            - Can you show me images of King Leopold II during his accession to the throne in 1865?
            - Do you have works created by Aimable Dutrieux? *And then you can ask the question:*
            - Who was this sculptor?
            - Can you show me images of Queen Marie-Henriette? Can you give me the authors of the images?
            - Can you show me the painting "The patriotic celebration of Belgium's fiftieth anniversary" created by Camille Van Camp?
            - Who are the people present in this painting?
            - Can you show me two engravings of the patriotic celebration of the fiftieth anniversary of Belgium created by Martin Claverie? From which newspapers do they come from?
            """)

            st.markdown("""

            #### Exemples de questions que vous pouvez poser

            FRANCAIS:

            - Quand est mort le roi Léopold Ier ? Avez-vous des images des funérailles ?
            - Avez-vous des images de la reine Elisabeth pendant la Première Guerre mondiale ?
            - Pouvez-vous me montrer le tableau "La revue des écoles" ? *Et ensuite vous pouvez poser la question :*
            - Qui a peint ce tableau ? *Et encore ensuite :*
            - Quelle est la dimension du tableau ? *Et encore ensuite :*
            - Qui est présent sur le tableau ? *Et encore ensuite :*
            - Pouvez-vous me montrer ce tableau avec une photo de la Wikimedia Commons et une autre photo de BALaT ?
            - Quand a eu lieu l'incendie du château de Laeken ? Avez-vous plusieurs images de cet événement ?
            - Quand s'est marié le roi Léopold Ier ? *L'assistant vous montrera une image du mariage.*
            - Pouvez-vous me montrer un portrait du roi Léopold Ier ? Il faut que ce soit une gravure.
            - Pouvez-vous me montrer plusieurs images du roi Léopold II ?
            - Pouvez-vous me montrer des images du roi Léopold II lors de son avènement en 1865 ?
            - Avez-vous des oeuvres réalisées par Aimable Dutrieux ? *Et ensuite vous pouvez poser la question :*
            - Qui était ce sculpteur ?
            - Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?
            - Pouvez-vous me montrer le tableau "La fête patriotique du cinquantenaire de la Belgique" réalisé par Camille Van Camp ?
            - Quelles sont les personnes présentes sur ce tableau ?
            - Pouvez-vous me montrer deux gravures de la fête patriotique du cinquantenaire de la Belgique réalisées par Martin Claverie ? De quel journal proviennent-elles ?
            - Avez-vous l'acte de décès de la princesse Joséphine ?
            - Pouvez-vous me montrer le tableau "Napoléon III et les souverains étrangers invités à l'Exposition universelle de 1867" ? *Et ensuite vous pouvez poser la question :*
            - Avez-vous un détail de ce tableau ?
            - Pouvez-vous me montrer des portraits réalisés par Franz Xaver Winterhalter ?
            - Où se trouve le tableau "La fête patriotique du cinquantenaire de la Belgique" peint par Camille Van Camp ?
            """)

            st.markdown(f"""
            _________
            Model: {st.session_state.model}. Vector size: 3072. Hybrid RAG with memory powered by Langchain. Web interface powered by Streamlit. *(c) Eric Dodémont, 2024.*
            """)

        elif page == "Admin" and password_ok == "yes":

            # # # # # # # # # # # # # # # # # # # # #
            # Side bar window: second page (Admin)  #
            # # # # # # # # # # # # # # # # # # # # #

            #st.title("Admin")

            model_list = ['OpenAI (2): gpt-4o-2024-05-13', 'OpenAI (1): gpt-4-turbo-2024-04-09', 'Google (2): gemini-1.5-pro-preview-0409', 'Google (1): gemini-1.0-pro-002', 'Anthropic: claude-3-opus-20240229', 'MetaAI: llama3-8b']
            st.session_state.model = st.selectbox('Choose a model: ', model_list)

            options = ['Scrape Commons', 'Scrape Europeana', 'Embed in DB']
            choice = st.sidebar.radio("Make your choice: ", options)

            if choice == "Scrape Europeana":
                st.write("Give the web page URL of an item from Europeana. The page will be scraped and saved in a JSON file.")
                url = st.text_input("URL: ")
                if url:
                    st.write(f"Scraping the web page...")
                    scrape_europeana_url(url)
                    st.write(f"Web page scraped and saved in a JSON file!")
            elif choice == "Scrape Commons":
                st.write("Give a category name from Wikimedia Commons. The pages will be scraped and saved in a JSON file.")
                category = st.text_input("Category: ")
                if category:
                    st.write(f"Scraping the web pages...")
                    scrape_commons_category(category)
                    st.write(f"Web pages scraped and saved in a JSON file!")
            elif choice == "Embed in DB":
                # Embed data in Chroma DB
                # Load and index

                JSON_FILES_DIR = "./json_files/"
                PDF_FILES_DIR = "./pdf_files/"

                # JSON files
                json_files = os.listdir(JSON_FILES_DIR)
                json_paths = []
                for json_file in json_files:
                    json_path = f"{JSON_FILES_DIR}{json_file}"
                    json_paths.append(json_path)

                # PDF files
                pdf_files = os.listdir(PDF_FILES_DIR)
                pdf_paths = []
                for pdf_file in pdf_files:
                    pdf_path = f"{PDF_FILES_DIR}{pdf_file}"
                    pdf_paths.append(pdf_path)

                if st.button("Start Embed"):
                    load_files_and_embed(json_paths, pdf_paths)
                    st.write("Done!")

                if st.button("Delete DB"):
                    delete_directory("./chromadb")
                    st.write("Done!")

                if st.button("List Files"):
                    path = './'
                    files = os.listdir(path)
                    st.write("Root path:")
                    st.write(files)
                    path = './chromadb'
                    files = os.listdir(path)
                    st.write("DB path:")
                    st.write(files)
                    file_path = './chromadb/chroma.sqlite3'
                    file_size = os.path.getsize(file_path)
                    st.write(f"DB size: {file_size} bytes")

    # # # # # # # # # # # #
    # Chat message window #
    # # # # # # # # # # # #

    with st.chat_message("assistant"):
        st.write("Hello! Bonjour! Hallo! 👋")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if question := st.chat_input("Enter your question / Entrez votre question / Voer uw vraag in"):
        # Display user message in chat message container
        st.chat_message("user").markdown(question)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})

        # Call the main chain (AI assistant). invoke is replaced by stream to stream the answer.
        answer_container = st.empty()
        answer = ""
        for chunk in ai_assistant_chain.stream({"input": question, "chat_history": st.session_state.chat_history}):
            answer_chunk = str(chunk.get("answer"))
            if answer_chunk != "None":  # Because it write NoneNone at the beginning 
                answer = answer + answer_chunk
                answer_container.write(answer)

        # Add Q/A to chat history for Langchain (chat_history)
        st.session_state.chat_history2.save_context({"input": question}, {"output": answer})
        load_memory = st.session_state.chat_history2.load_memory_variables({})
        st.session_state.chat_history = load_memory["history"]

        # Add Answer to chat history for Streamlit (messages)
        st.session_state.messages.append({"role": "assistant", "content": answer})
