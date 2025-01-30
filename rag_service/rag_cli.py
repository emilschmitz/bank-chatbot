import os
import json
import warnings
import requests
from pathlib import Path
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores.redis import Redis as RedisVectorStore
from langchain.schema import Document as LC_Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import redis

load_dotenv()
warnings.filterwarnings("ignore")

# -------------------------------------------------------------------
# 1. Load JSON with document titles/URLs
# -------------------------------------------------------------------
JSON_FILE = "docs/documents_sk_ostprignitz.json"
with open(JSON_FILE, "r", encoding="utf-8") as f:
    docs_dict = json.load(f)

# -------------------------------------------------------------------
# 2. Download and convert docs to text
#    (Replace with your actual PDF->text or docling logic)
# -------------------------------------------------------------------
def fetch_document_as_text(title, url, download_dir="downloads"):
    dl_dir = Path(download_dir)
    dl_dir.mkdir(exist_ok=True)
    local_file = dl_dir / f"{title}.pdf"  # or .xls etc. as needed

    # Download if not exists
    if not local_file.exists():
        resp = requests.get(url)
        with open(local_file, "wb") as wf:
            wf.write(resp.content)
    
    # TODO: Convert PDF/Excel/etc. to text. Here: a dummy placeholder
    text_data = f"Dummy text for {title}, originally downloaded from {url}"
    return text_data

# -------------------------------------------------------------------
# 3. Chunk text for vector storage
# -------------------------------------------------------------------
def create_chunks(title, url, text, chunk_size=1000, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return [Document(page_content=f"Dokumentname: {title}\n\n Link: {url} \n\n Textstueck: {chunk}") for chunk in splitter.split_text(text)]

# -------------------------------------------------------------------
# 4. Create embeddings and store in Redis
# -------------------------------------------------------------------
def store_docs_in_redis(all_docs):
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")
    redis_store = RedisVectorStore.from_documents(
        documents=all_docs,
        embedding=embeddings,
        redis_url="redis://localhost:6379",
        index_name="sparkasse_index",  # name your index
    )
    return redis_store

# -------------------------------------------------------------------
# 5. Simple RAG chain
# -------------------------------------------------------------------
def create_rag_chain(retriever):
    prompt = """
    Du bist ein Assistent für die Sparkasse und beantwortest Fragen. Nutze den untenstehenden Kontext, um genau zu antworten.
    Wenn du es nicht weißt, sag es. Antworte in Stichpunkten. Benenne immer deine Quellen mit Dokumentnamen und Link, z.B. 'Lesen Sie mehr zum Them in..."

    Frage: {question}
    Kontext: {context}
    Antwort:
    """
    # Use DeepSeek locally via Ollama
    model = ChatOllama(model="deepseek-r1:1.5b", base_url="http://localhost:11434")
    template = ChatPromptTemplate.from_template(prompt)
    # For RAG streaming
    chain = (
        {
            "context": retriever | (lambda docs: "\n\n".join([d.page_content for d in docs])),
            "question": RunnablePassthrough()
        }
        | template
        | model
        | StrOutputParser()
    )
    return chain

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
if __name__ == "__main__":
    # 1) Download + convert all docs to text, chunk them
    all_chunks = []
    for title, url in docs_dict.items():
        text_data = fetch_document_as_text(title, url)
        doc_chunks = create_chunks(text_data)
        # Make sure each chunk is annotated
        for i, c in enumerate(doc_chunks):
            c.metadata["source"] = title
            c.metadata["chunk_idx"] = i
        all_chunks.extend(doc_chunks)
    
    # 2) Store everything in Redis
    redis_store = store_docs_in_redis(all_chunks)
    retriever = redis_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    # 3) Build RAG chain
    rag_chain = create_rag_chain(retriever)

    # 4) Demo Q&A
    questions = [
        "Was steht in der Existenzgründerbroschüre?",
        "Worum geht es in der Selbstauskunft?"
    ]
    for q in questions:
        print(f"\nQuestion: {q}")
        for token in rag_chain.stream(q):
            print(token, end="", flush=True)
        print("\n" + "-" * 40)
