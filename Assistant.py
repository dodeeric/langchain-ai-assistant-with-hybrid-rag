#!/usr/bin/env python

"""
Ragai - (c) Eric Dodémont, 2024.
This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art
and the Belgian monarchy. To answer, the assistant queries the graphic databases.
Topology: backend = langchain (RAG + LLM), frontend = streamlit (chatbot + admin), assistant = main()
Start the app: streamlit run assistant.py
"""

# History:
# v2: with chat history
# v3: with PDF indexation
# v31/v32: JSON and PDF indexation with function
# v5: with a limit of messages in the chat history
# v6: load chunks only from DB on disk
# v7: diplay question examples in the expander
# v8: ollama (llama3, mistral, etc.) + anthropic claude + google vertexai
# v9: multiselect box to chose the model
# v10: import one function --> one module
# v11: assistant: main() + assistant_frontend (streamlit) + assistant_backend (langchain) --> two modules

import dotenv

from modules.assistant_frontend_v10 import assistant_frontend


dotenv.load_dotenv()


def main():
    """
    This is the main module: it will start the frontend (straemlit web interface) and
    backend (langchain AI assistant).
    """

    assistant_frontend()


if __name__ == "__main__":
    main()
