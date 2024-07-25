#!/usr/bin/env python

# RagAiAgent - (c) Eric Dodémont, 2024.

"""
This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art
and the Belgian monarchy. To answer, the assistant queries graphic databases.
Topology: backend = langchain/langgraph (RAG search + Web search + LLM), frontend = streamlit (chatbot + admin), assistant = main()
Start the app: streamlit run assistant.py
"""

import dotenv

from modules.assistant_frontend import assistant_frontend


dotenv.load_dotenv()


def main():
    """
    This is the main module: it will start the frontend (straemlit web interface) and
    backend (langchain/langgraph AI assistant).
    """

    assistant_frontend()


if __name__ == "__main__":
    main()
