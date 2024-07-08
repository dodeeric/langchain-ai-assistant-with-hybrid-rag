#!/usr/bin/env python

# Ragai - (c) Eric Dodémont, 2024.

"""
This function runs the frontend web interface.
"""

import streamlit as st
from langchain.memory import ConversationBufferWindowMemory

from modules.assistant_backend import instanciate_ai_assistant_chain
from config.config import *


# Function defined in two files: should be moved in a module
def reset_conversation():
    """
    Reset the conversation: clear the chat history and clear the screen.
    """

    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.chat_history2 = ConversationBufferWindowMemory(k=MAX_MESSAGES_IN_MEMORY, return_messages=True)


def assistant_frontend():
    """
    All related to Streamlit for the main page (about & chat windows) and connection with the Langchain backend.
    """

    st.set_page_config(page_title=ASSISTANT_NAME, page_icon=ASSISTANT_ICON)
    
    # Initialize chat history (chat_history) for LangChain
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history2 = ConversationBufferWindowMemory(k=MAX_MESSAGES_IN_MEMORY, return_messages=True)   # Max k Q/A in the chat history for Langchain

    # Initialize chat history (messages) for Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL

    if "temperature" not in st.session_state:
        st.session_state.temperature = DEFAULT_TEMPERATURE

    if "password_ok" not in st.session_state:
        st.session_state.password_ok = False

    if "input_password" not in st.session_state:
        st.session_state.input_password = ""

    # Load, index, retrieve and generate

    ai_assistant_chain = instanciate_ai_assistant_chain(st.session_state.model, st.session_state.temperature)

    # # # # # # # #
    # Main window #
    # # # # # # # #

    st.image(LOGO_PATH, use_column_width=True)

    st.markdown(f"## {ASSISTANT_NAME}")
    st.caption("💬 A chatbot powered by Langchain and Streamlit")

    # # # # # # # # # # # # # #
    # Side bar window (About) #
    # # # # # # # # # # # # # #

    with st.sidebar:

        st.write(f"Model: {st.session_state.model} ({st.session_state.temperature})")
        st.write(ABOUT_TEXT)
        st.write(SIDEBAR_FOOTER)

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
