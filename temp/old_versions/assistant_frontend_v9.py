#!/usr/bin/env python

"""
This function runs the frontend web interface.
"""

# v2: stream output
# v3: integrate admin in main web interface
# v4: move model selection to admin interface + move files dir to json_files + add admin password
# v5: add a slider for the temperature + errors catch + use config.py
# v6: move out 2 functions to utils module + only 4 LLMs + model menu in config.py
# v7: corrected menu switch (about/admin) + display model in use
# v8: upload a file + upload a pdf file + display total number of pages (web + pdf)
# v9: scape web pages (not only commons categories or europeana)

import streamlit as st
from langchain.memory import ConversationBufferWindowMemory
import os

from modules.web_scraping_utils_v1 import scrape_commons_category, scrape_web_page_url
from modules.assistant_backend_v2 import instanciate_ai_assistant_chain
from modules.utils_v1 import load_files_and_embed, delete_directory
from config.config import *


def reset_conversation():
    """
    Reset the conversation: clear the chat history and clear the screen.
    """

    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)


def assistant_frontend():
    """
    All related to Streamlit and connection with the Langchain backend. Includes also the admin interface.
    """

    st.set_page_config(page_title=ASSISTANT_NAME, page_icon=ASSISTANT_ICON)
    
    # Initialize chat history (chat_history) for LangChain
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history2 = ConversationBufferWindowMemory(k=4, return_messages=True)   # Max k Q/A in the chat history for Langchain

    # Initialize chat history (messages) for Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL

    if "temperature" not in st.session_state:
        st.session_state.temperature = DEFAULT_TEMPERATURE

    if "password_ok" not in st.session_state:
        st.session_state.password_ok = False
        st.session_state.page = "About"

    # Load, index, retrieve and generate

    ai_assistant_chain = instanciate_ai_assistant_chain(st.session_state.model, st.session_state.temperature)

    # # # # # # # #
    # Main window #
    # # # # # # # #

    st.image(LOGO_PATH, use_column_width=True)

    st.markdown(f"## {ASSISTANT_NAME}")
    st.caption("💬 A chatbot powered by Langchain and Streamlit")

    # # # # # # # # # #
    # Side bar window #
    # # # # # # # # # #

    with st.sidebar:

        st.write(f"Model: {st.session_state.model} ({st.session_state.temperature})")

        st.session_state.page = st.radio("Go to page:", ["About", "Admin"])

        # Ask admin password to access admin menu
        admin_password = os.getenv("ADMIN_PASSWORD", "YYYY")
        password = st.text_input("Enter admin password: ", type="password")
        if password != admin_password:
            st.session_state.password_ok = False
            #st.write("Wrong password!")
        else:
            st.session_state.password_ok = True

        # Side bar: first or second page
        if st.session_state.page == "About":
        
            # # # # # # # # # # # # # # # # # # # #
            # Side bar window: first page (About) #
            # # # # # # # # # # # # # # # # # # # #

            st.write(ABOUT_TEXT)

            st.write(SIDEBAR_FOOTER)

        elif st.session_state.page == "Admin" and st.session_state.password_ok:

            # # # # # # # # # # # # # # # # # # # # #
            # Side bar window: second page (Admin)  #
            # # # # # # # # # # # # # # # # # # # # #

            model_list = [OPENAI_MENU, ANTHROPIC_MENU, VERTEXAI_MENU, OLLAMA_MENU]
            st.session_state.model = st.selectbox('Model: ', model_list, DEFAULT_MENU_CHOICE)

            st.session_state.temperature = st.slider("Temperature: ", 0.0, 2.0, DEFAULT_TEMPERATURE)
            st.caption("OpenAI: 0-2, Anthropic: 0-1")
            
            options = ['Upload PDF Files', 'Scrape Web Pages', 'Scrape Web Pages from Wikimedia Commons', 'Embed Pages in DB', 'Upload Files']
            choice = st.sidebar.radio("Make your choice: ", options)

            if choice == "Scrape Web Pages":
                st.caption("Give the web page URL and the filter (CSS class). The page will be scraped and saved in a JSON file.")
                st.caption("filter: two-third last (balat / irpa), media-body (belgica / kbr), hproduct commons-file-information-table \
                           (commons / wikimedia: summary or description section), card metadata-box-card mb-3 (europeana / kul, irpa, etc.)")
                url = st.text_input("URL: ")
                filter = st.text_input("Filter: ")
                if url and filter:
                    st.write(f"Scraping the web page...")
                    scrape_web_page_url(url, filter)
                    st.write(f"Web page scraped and saved in a JSON file!")
            elif choice == "Scrape Web Pages from Wikimedia Commons":
                st.caption("Give a category name from Wikimedia Commons. The pages will be scraped and saved in a JSON file.")
                category = st.text_input("Category: ")
                if category:
                    st.write(f"Scraping the web pages...")
                    scrape_commons_category(category)
                    st.write(f"Web pages scraped and saved in a JSON file!")
            elif choice == "Upload Files":
                st.caption("Upload a file in the root directory.")
                uploaded_file = st.file_uploader("Choose a file:")
                if uploaded_file is not None:
                    bytes_data = uploaded_file.getvalue()
                    file_name = uploaded_file.name
                    with open(file_name, "wb") as file:
                        file.write(bytes_data)
                    st.success(f"File '{file_name}' uploaded and saved successfully!")
                else:
                    st.warning("No file uploaded yet.")
            elif choice == "Upload PDF Files":
                st.caption("Upload a PDF file in the 'pdf_files' directory.")
                uploaded_file = st.file_uploader("Choose a PDF file:", type=["pdf"])
                if uploaded_file is not None:
                    bytes_data = uploaded_file.getvalue()
                    file_name = uploaded_file.name
                    with open(f"./pdf_files/{file_name}", "wb") as file:
                        file.write(bytes_data)
                    st.success(f"File '{file_name}' uploaded and saved successfully!")
                else:
                    st.warning("No file uploaded yet.")  
            elif choice == "Embed Pages in DB":
                # Embed data in Chroma DB
                # Load and index

                st.caption('Embed in the vector DB all the web and pdf pages.')

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
                    load_files_and_embed(json_paths, pdf_paths, embed=True)
                    st.write("Done!")

                if st.button("Delete DB"):
                    delete_directory("./chromadb")
                    st.write("Done!")

                if st.button("Clear Memory and Streamlit Cache"):
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    reset_conversation()
                    st.write("Done!")

                if st.button("Files and DB Info"):

                    load_files_and_embed(json_paths, pdf_paths, embed=False)

                    try:

                        file_path = './chromadb/chroma.sqlite3'
                        file_size = os.path.getsize(file_path)
                        file_size = file_size / 1024  # In KB
                        if file_size > 144:
                            st.write(f"DB size: {file_size} KB")
                        else:
                            st.write(f"DB size: {file_size} KB. DB is empty!")

                        path = './'
                        files = os.listdir(path)
                        st.write("Root path:")
                        st.write(files)

                        path = './chromadb'
                        files = os.listdir(path)
                        st.write("DB path:")
                        st.write(files)

                    except Exception as e:
                        st.write("Error: Is the DB available?")
                        st.write(f"Error: {e}")

    # # # # # # # # # # # #
    # Chat message window #
    # # # # # # # # # # # #

    with st.chat_message("assistant"):
        st.write(HELLO_MESSAGE)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if question := st.chat_input(USER_PROMPT):
        # Display user message in chat message container
        st.chat_message("user").markdown(question)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": question})

        try:

            # Call the main chain (AI assistant). invoke is replaced by stream to stream the answer.
            answer_container = st.empty()
            answer = ""
            for chunk in ai_assistant_chain.stream({"input": question, "chat_history": st.session_state.chat_history}):
                answer_chunk = str(chunk.get("answer"))
                if answer_chunk != "None":  # Because it write NoneNone at the beginning 
                    answer = answer + answer_chunk
                    answer_container.write(answer)

        except Exception as e:
            st.write("Error: Cannot invoke/stream the main chain!")
            st.write(f"Error: {e}")

        # Add Q/A to chat history for Langchain (chat_history)
        st.session_state.chat_history2.save_context({"input": question}, {"output": answer})
        load_memory = st.session_state.chat_history2.load_memory_variables({})
        st.session_state.chat_history = load_memory["history"]

        # Add Answer to chat history for Streamlit (messages)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Clear the conversation
        st.button(NEW_CHAT_MESSAGE, on_click=reset_conversation)
