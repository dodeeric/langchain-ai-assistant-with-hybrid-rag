#!/usr/bin/env python

# v2: with chat history
# v3: with PDF indexation
# v31/v32: JSON and PDF indexation with function
# v5: with a limit of messages in the chat history
# v6: load chunks only from DB on disk
# v7: diplay question examples in the expander
# v8: ollama (llama3, mistral, etc.) + anthropic claude + google vertexai
# v9: multiselect box to chose the model
# v10: main() function + import two functions

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art  #
# and the Belgian monarchy. To answer, the assistant queries the graphic databases BALaT of the IRPA  #
# (Royal Institute of Artistic Heritage), Belgica of the KBR (Royal Library) and Wikimedia Commons.   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Only to be able to run on Github Codespace
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import dotenv, jq, time
import streamlit as st
from PIL import Image
from langchain.memory import ConversationBufferWindowMemory
from assistant_module_v1 import instanciate_vector_db, instanciate_ai_assistant_chain

dotenv.load_dotenv()

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

#vector_db = instanciate_vector_db()

ai_assistant_chain = instanciate_ai_assistant_chain(st.session_state.model)

#with st.expander("Examples of questions you can ask | Exemples de questions que vous pouvez poser"):
#    
#    st.markdown("""
#    xxx
#    """)

logo = Image.open("./image.jpg")
st.image(logo, use_column_width=True)

#st.set_page_config(page_title="BMAE", page_icon="👑")
#st.title("Belgian Monarchy Artworks Explorer")
st.markdown("## Belgian Monarchy Artworks Explorer")
st.caption("💬 A chatbot powered by Langchain and Streamlit")

with st.sidebar:

    model_list = ['OpenAI (2): gpt-4o-2024-05-13', 'OpenAI (1): gpt-4-turbo-2024-04-09', 'Google (2): gemini-1.5-pro-preview-0409', 'Google (1): gemini-1.0-pro-002', 'Anthropic: claude-3-opus-20240229', 'MetaAI: llama3-8b']
    st.session_state.model = st.selectbox('Choose a model | Choisissez un modèle | Kies een model: ', model_list)
    #st.write('You selected | Vous avez sélectionné | Jij hebt geselecteerd: ', st.session_state.model)

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
    - Avez-vous des images de la reine Elisabeth pendant la Premierre Guerre mondiale ?
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
    - Qui était ce sculteur ?
    - Pouvez-vous me montrer des images sur lesquelles ce trouve la reine Marie-Henriette ? Pouvez-vous me donner les auteurs des images ?
    - Pouvez-vous me montrer le tableau "La fête patriotique du cinquantenaire de la Belgique" réalisé par Camille Van Camp ?
    - Quelles sont les personnes présentes sur ce tableau ?
    - Pouvez-vous me montrer deux gravures de la fête patriotique du cinquantenaire de la Belgique réalisées par Martin Claverie ? De quel journal proviennent-elles ?
    """)

    st.markdown("""
    _________
    Vector size: 3072. Hybrid RAG with memory powered by Langchain. Web interface powered by Streamlit. *(c) Eric Dodémont, 2024.*
    """)

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

    # Call the main chain
    output = ai_assistant_chain.invoke({"input": question, "chat_history": st.session_state.chat_history}) # output is a dictionary. output["answer"] is the LLM answer in markdown format.
    
    st.session_state.chat_history2.save_context({"input": question}, {"output": output["answer"]})
    load_memory = st.session_state.chat_history2.load_memory_variables({})
    st.session_state.chat_history = load_memory["history"]
        
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(output["answer"])
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": output["answer"]})

# $ streamlit run assistant.py &
# $ sudo streamlit run assistant.py --server.port 80 > assistant.log 2>&1 &
