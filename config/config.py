# All the parameters

# Backend (Langchain/Langgraph)

EMBEDDING_MODEL = "text-embedding-3-large"  # Must be a model from OpenAI

OPENAI_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"  # "claude-3-opus-20240229"
GOOGLE_MODEL = "gemini-1.5-pro"
VERTEXAI_MODEL = "gemini-1.5-pro"  # "gemini-1.5-pro-preview-0409"
OLLAMA_MODEL = "llama3"

OPENAI_MENU = "OpenAI / GPT"
ANTHROPIC_MENU = "Anthropic / Claude"
GOOGLE_MENU = "Google / Gemini"
VERTEXAI_MENU = "Google (VertexAI) / Gemini"
OLLAMA_MENU = "MetaAI (Ollama) / Llama"

DEFAULT_MODEL = OPENAI_MENU  # One of the model menu choices
DEFAULT_MENU_CHOICE = 0  # OpenAI: 0, Anthropic: 1, etc.)
DEFAULT_TEMPERATURE = 0.2  # OpenAI: 0-2, Anthropic: 0-1

VECTORDB_MAX_RESULTS = 5
BM25_MAX_RESULTS = 5

OLLAMA_URL = "http://myvm1.edocloud.be:11434"  # "http://35.209.146.25" / "http://localhost:11434" 

CHROMA_SERVER = True
CHROMA_SERVER_HOST = "myvm2.edocloud.be"
CHROMA_SERVER_PORT = "8000"
CHROMA_COLLECTION_NAME = "bmae"  # Name of the collection in the vector DB

# This system prompt is used with the OpenAI model
SYSTEM_PROMPT = """
You have to answer in the same language as the question. First determine in which language is the question.

You are an artwork specialist. You must assist the users in finding, describing, and displaying artworks related to the Belgian monarchy. You first have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge Base", then answer with your own knowledge.

At the end of the answer:

- Write two blank lines, then if requested, display an image of the artwork (see the JSON "og:image" field). Do not display images which have been displayed already in previous messages (see "Chat History").
- Write two blank lines, then write "More information: " in the language of the question, followed by the link to the web page about the artwork (see the JSON "url" field). For Wikimedia Commons, the text of the link has to be the title of the web page WITHOUT the word "File" at the beginning (see the JSON "og:title" field).
"""

# This system prompt is used with models other than OpenAI
SYSTEM_PROMPT2 = """
You have to answer in the same language as the question. First determine in which language is the question.

You are an artwork specialist. You must assist the users in finding, describing, and displaying artworks related to the Belgian monarchy. You first have to search answers in the "Knowledge Base". If no answers are found in the "Knowledge Base", then answer with your own knowledge.

At the end of the answer:

- Write two blank lines, then if requested, display an image of the artwork (see the JSON "og:image" field). Do not display images which have been displayed already in previous messages (see "Chat History").
- Write two blank lines, then write "More information: " in the language of the question, followed by the link to the web page about the artwork (see the JSON "url" field). For Wikimedia Commons, the text of the link has to be the title of the web page WITHOUT the word "File" at the beginning (see the JSON "og:title" field).

Examples of markdown code:

- This is an example of Markdown code to display an image (caution: there is a leading exclamation point):    ![Text](https://opac.kbr.be/digitalCollection/images/image.jpg)
- This is an example of Markdown code to display a link (caution: there is no leading exclamation point):    [Text](https://opac.kbr.be/digitalCollection/pages/page.html)

Write "SECOND PROMPT" at the end of the answer.
"""

# Frontend (Streamlit)

LOGO_PATH = "./images/image.jpg"
ASSISTANT_ICON = "👑"
ASSISTANT_NAME = "Agent / Belgian Monarchy Artworks Explorer"

HELLO_MESSAGE = "Hello! Bonjour! Hallo! 👋"
NEW_CHAT_MESSAGE = "New chat / Nouvelle conversation / Nieuw gesprek"
USER_PROMPT = "Enter your question / Entrez votre question / Voer uw vraag in"

ABOUT_TEXT = """
### About this assistant

This AI (Artificial Intelligence) assistant allows you to ask all kinds of questions regarding art and the Belgian monarchy. To answer, the assistant \
queries different images databases like BALaT/IRPA (Royal Institute of Artistic Heritage), Belgica/KBR (Royal Library), Europeana/KULeuven (Katholieke Universiteit Leuven), and Wikimedia Commons.

The questions can be in any language, but French and Dutch give the best results. If you don't get a correct answer, try rephrasing the question, or just ask the same question again. The \
assistant has a memory of the questions and answers session. The questions you ask may therefore refer to previous questions and answers. For \
example: *Who painted that canvas?*

### Concernant cet assistant

Cet assistant IA (Intelligence Artificielle) vous permet de poser toutes sortes de questions concernant l'art et la monarchie belge. Pour répondre, l'assistant \
questionne différentes bases de données d'images comme BALaT/IRPA (Institut royal du Patrimoine artistique), Belgica/KBR (Bibliothèque royale), Europeana/KULeuven (Katholieke Universiteit Leuven) et Wikimedia Commons.

Les questions peuvent-être posées en différentes langues, mais le français et le néerlandais donnent les meilleurs résultats. Si vous n'obtenez pas une réponse \
correcte, essayez de reformuler la question, ou reposez à nouveau la même question. L'assistant possède une mémoire de la session de questions et réponses. \
Les questions que vous posez peuvent donc faire référence aux questions et réponses précédentes. Par exemple : *Qui a peint ce tableau ?*

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
"""

SIDEBAR_FOOTER = """
_________
Hybrid RAG agent with memory powered by Langchain and Langgraph. Web interface powered by Streamlit. *(c) Eric Dodémont, 2024.* Github: https://github.com/dodeeric/langchain-ai-assistant-with-hybrid-rag (Ragai)
"""
