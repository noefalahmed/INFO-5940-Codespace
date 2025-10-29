import streamlit as st
import os, uuid, hashlib
import base64
from typing import List
from openai import OpenAI
# Document loaders
from langchain_community.document_loaders import TextLoader, PyPDFLoader

# Text splitter
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Embeddings
from langchain_community.embeddings import OpenAIEmbeddings

# Vector store
from langchain_community.vectorstores import Chroma

# Chat / LLM
from langchain_community.chat_models import ChatOpenAI

# Conversational chain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain


def load_documents(file_paths: List[str]):
    docs = []
    for fp in file_paths:
        name = os.path.basename(fp)
        if fp.lower().endswith(".txt"):
            loader = TextLoader(fp, encoding="utf-8")
            cur_docs = loader.load()
        elif fp.lower().endswith(".pdf"):
            loader = PyPDFLoader(fp)
            cur_docs = loader.load()
        else:
            st.warning(f"Skipping unsupported file: {fp}")
            continue
        for d in cur_docs:
            d.metadata["source"] = name
        docs.extend(cur_docs)
    return docs


def chunk_documents(docs, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_documents(docs)


def dedupe_and_prepare(chunks):
    texts, metadatas, ids = [], [], []
    seen_hashes = set()
    for i, c in enumerate(chunks):
        text = c.page_content.strip()
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        meta = dict(c.metadata)
        meta.update({"chunk_index": i, "chunk_hash": h})
        texts.append(text)
        metadatas.append(meta)
        ids.append(str(uuid.uuid4()))
    return texts, metadatas, ids


def index_to_chroma(texts, metadatas, ids, persist_directory="chroma_db", collection_name="docs"):
    embeddings = OpenAIEmbeddings(
        model="openai.text-embedding-3-large",
        openai_api_key="sk-uWotNb8a6pRiG_jq835X_w"
    )
    db = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        ids=ids,
        collection_name=collection_name,
        persist_directory=persist_directory
    )
    db.persist()
    return db


def format_chat_history(messages):
    history = []
    for i in range(0, len(messages) - 1, 2):
        user_msg = messages[i]["content"]
        assistant_msg = messages[i + 1]["content"] if i + 1 < len(messages) else ""
        history.append((user_msg, assistant_msg))
    return history



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&display=swap');
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #05090F;
    color: rgb(244, 234, 217);
}
.chat-card {
    max-width: 850px;
    margin: 2rem auto;
    padding: 2rem;
    background-color: #05090F;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.7);
}
.chat-header {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 400;
    font-size: 44px;
    margin-bottom: 1rem;
    color: rgb(244, 234, 217);
}
.stFileUploader>div>div>input {
    display: inline-block;
    margin-right: 1rem;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}
.user-bubble, .assistant-bubble {
    padding: 0.8rem 1rem;
    border-radius: 16px;
    margin: 0.5rem 0;
    max-width: 75%;
    opacity: 0;
    animation: fadeIn 0.5s forwards;
}
.user-bubble {
    background-color: #101820;
    color: rgb(244, 234, 217);
    text-align: right;
    float: right;
    clear: both;
}
.assistant-bubble {
    background-color: #11171E;
    color: rgb(244, 234, 217);
    text-align: left;
    float: left;
    clear: both;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# Load SVG as base64
with open("a.svg", "rb") as f:
    svg_data = f.read()
svg_base64 = base64.b64encode(svg_data).decode("utf-8")
svg_src = f"data:image/svg+xml;base64,{svg_base64}"

# Chat card & header with icon
st.markdown('<div class="chat-card">', unsafe_allow_html=True)
st.markdown(f'''
<div class="chat-header">
    <img src="{svg_src}" alt="icon"> Noefal's RAG Chatbot
</div>
''', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload .txt or .pdf files",
    type=["txt", "pdf"],
    accept_multiple_files=True
)

client = OpenAI(
    api_key="sk-uWotNb8a6pRiG_jq835X_w",
    base_url="https://api.ai.it.cornell.edu"
)

# Initialize message history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Upload a file and ask a question about it!"}
    ]

# Display chat history
for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

question = st.chat_input("Ask something about the uploaded document(s)")


db = None
if uploaded_files:
    os.makedirs("data", exist_ok=True)
    file_paths = []
    for file in uploaded_files:
        path = os.path.join("data", file.name)
        with open(path, "wb") as f:
            f.write(file.getbuffer())
        file_paths.append(path)

    with st.spinner("Processing documents..."):
        docs = load_documents(file_paths)
        chunks = chunk_documents(docs)
        texts, metas, ids = dedupe_and_prepare(chunks)
        db = index_to_chroma(
            texts, metas, ids,
            persist_directory="./chroma_db",
            collection_name="uploaded_docs"
        )



if not uploaded_files:
    st.info("Please upload at least one .txt or .pdf file to start.")
elif not question:
    st.info("Type a question about the uploaded document(s) to get an answer.")
elif question and db:
    st.session_state.messages.append({"role": "user", "content": question})
    st.markdown(f'<div class="user-bubble">{question}</div>', unsafe_allow_html=True)

    retriever = db.as_retriever(search_kwargs={"k": 3})
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(
            model="openai.gpt-4o-mini",
            openai_api_key="sk-uWotNb8a6pRiG_jq835X_w"
        ),
        retriever=retriever
    )

    chat_history_formatted = format_chat_history(st.session_state.messages)
    result = qa_chain({"question": question, "chat_history": chat_history_formatted})
    answer = result["answer"]

    st.markdown(f'<div class="assistant-bubble">{answer}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown('</div>', unsafe_allow_html=True)
