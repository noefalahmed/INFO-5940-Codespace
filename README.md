# Noefal's RAG Chatbot

A Streamlit-based Retrieval-Augmented Generation (RAG) chatbot that ingests PDF and TXT files, creates embeddings, and answers user queries with cited sources.

## Features and Design

### File Handling
- Supported file types: `.pdf` (parsed page-by-page) and `.txt` (fully decoded).
- Each document stores metadata: `source=filename` for text, and `page=i` for PDFs.
- Skips unsupported files automatically.
- Multiple files can be uploaded simultaneously.
- Uploaded files are saved in a local `data` folder.

### Chunking and Deduplication
- Uses `RecursiveCharacterTextSplitter` (chunk_size=1000, chunk_overlap=200) to split text into semantically coherent chunks.
- Deduplicates chunks by SHA-256 hash to avoid repeated content.
- Each chunk includes metadata: original source, chunk index, and hash.

### Embeddings and Indexing
- Embeddings: OpenAI `text-embedding-3-large` via `OpenAIEmbeddings`.
- Vector store: `Chroma` (stored in `./chroma_db`, collection name `uploaded_docs`).
- Persistent database ensures faster reloading while keeping indexing simple and local.
- Retrievers: top-3 similarity search for efficient recall.

### Chat and Conversational Memory
- LLM: `gpt-4o-mini` via `ChatOpenAI` with low temperature for stable answers.
- Chat history is formatted as user-assistant pairs for contextual follow-ups.
- User questions trigger retrieval and answer generation, with results displayed in styled chat bubbles.
- Initial message guides the user: *“Upload a file and ask a question about it!”*

### User Interface
- Custom styling using IBM Plex fonts and dark mode theme.
- Chat bubbles distinguish between user and assistant.
- Chat header includes base64-encoded SVG icon.
- Spinner shows during document processing and indexing.
- Input disabled until files are uploaded and processed.

### Error Handling
- Warns if unsupported or unreadable files are uploaded.
- Gracefully handles empty or invalid files.
- Prevents hallucinations by answering only based on uploaded content.

### Limitations
- No OCR for scanned PDFs.
- In-memory index and local `Chroma` persistence only.
- Citation shows source file and page but not exact text span.

## Prerequisites
- Python 3.11+
- OpenAI API key (do **not** hard-code in production)
- Dependencies listed in `requirements.txt`

## Quick Start

1. Install dependencies:
```bash
python3 -m pip install -r requirements.txt
````

2. Set OpenAI API Key:

```bash
export OPENAI_API_KEY="sk-..."
```

3. Run Streamlit app:

```bash
streamlit run chat_with_pdf.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

1. Upload one or more `.pdf` or `.txt` files.
2. Wait for the app to process and index files.
3. Ask questions in the chat; answers include citations.
4. Uploading new files automatically clears the old index.

## Implementation Details

* **Chunking:** `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`
* **Deduplication:** SHA-256 hash check for repeated content
* **Embeddings:** OpenAI `text-embedding-3-large`
* **Vector Store:** Chroma
* **Retriever:** Top-3 similarity search
* **Chat Memory:** Formatted user-assistant pairs
* **Styling:** IBM Plex fonts, dark theme, fade-in chat bubbles

## Troubleshooting

* If imports fail:

```bash
python3 -m pip install -U -r requirements.txt
```

* Embeddings fail: check `OPENAI_API_KEY` and internet connectivity.
* PDFs show no text: likely scanned — use OCR first.
* Environment check:

```bash
python3 -c "import langchain_community; print(langchain_community.__version__)"
python3 -m pip list | grep -i langchain
echo $OPENAI_API_KEY
```
