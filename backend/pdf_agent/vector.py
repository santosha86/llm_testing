from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

# Use absolute paths based on script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "pdfs")
DB_LOCATION = os.path.join(SCRIPT_DIR, "chroma_langchain_db")

embeddings = OllamaEmbeddings(model="qwen3-embedding")

# 🔎 Test embeddings early
test_embed = embeddings.embed_query("hello")
if not test_embed:
    raise RuntimeError("Ollama embeddings returned empty vector. Check Ollama model.")

# Check BEFORE creating Chroma instance (Chroma auto-creates the folder)
db_exists = os.path.exists(DB_LOCATION)
print(f"DEBUG: DB_LOCATION = {DB_LOCATION}")
print(f"DEBUG: db_exists = {db_exists}")

vector_store = Chroma(
    collection_name="pdf_knowledge_base",
    persist_directory=DB_LOCATION,
    embedding_function=embeddings
)

if not db_exists:
    loader = PyPDFDirectoryLoader(DATA_FOLDER)
    raw_docs = loader.load()

    if not raw_docs:
        raise RuntimeError("No PDF documents loaded. Check DATA_FOLDER.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(raw_docs)

    if not chunks:
        raise RuntimeError("No text chunks created from PDFs.")

    vector_store.add_documents(chunks)
    print(f"Indexed {len(chunks)} chunks into Chroma")
else:
    print("ℹVector DB already exists")

retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)
