import json
import os
import redis
import requests
import logging
from pathlib import Path
from markitdown import MarkItDown # type: ignore
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

ollama_host = os.getenv("OLLAMA_HOST", "localhost")  
redis_host = os.getenv("REDIS_HOST", "localhost")

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Initialize Redis connection
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)

# Initialize embeddings
embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url=f"http://{ollama_host}:11434")
VECTOR_DIM = len(embeddings.embed_query('This is just to get embedding length')) # Dimension of embeddings

class DocumentProcessor:
    def __init__(self, download_dir="./docs/downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.md_converter = MarkItDown()
        logging.info(f"Initialized DocumentProcessor with directory: {download_dir}")
        
    def download_document(self, title, url):
        logging.info(f"Downloading: {title}")
        extension = url.split('.')[-1].lower()
        local_file = self.download_dir / f"{title}.{extension}"
  
              
        if not local_file.exists():
            response = requests.get(url)
            with open(local_file, "wb") as f:
                f.write(response.content)
        
        return local_file
    
    def convert_to_markdown(self, file_path):
        """Convert document to markdown format using MarkItDown"""
        logging.info(f"Converting to markdown: {file_path}")
        result = self.md_converter.convert(str(file_path))
        return result.text_content
    
    def split_markdown(self, markdown_content):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3")
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
        chunks = splitter.split_text(markdown_content)
        logging.info(f"Split markdown into {len(chunks)} chunks")
        return chunks

def create_index():
    logging.info("Creating new search index")
    try:
        redis_client.ft('docs').dropindex(delete_documents=True)  # Clear old data
    except:
        pass

    schema = (
        TextField("$.text", as_name="text"),  # Add back $. prefix
        TextField("$.title", as_name="title"),
        TextField("$.url", as_name="url"),
        VectorField("$.embedding",  # Add back $. prefix
                   "HNSW", {
                       "TYPE": "FLOAT32",
                       "DIM": VECTOR_DIM,
                       "DISTANCE_METRIC": "COSINE"
                   }, as_name="embedding")
    )

    redis_client.ft('docs').create_index(
        schema,
        definition=IndexDefinition(prefix=["doc:"], index_type=IndexType.JSON)
    )
    logging.info(f"Index created with dimension {VECTOR_DIM}")

def ingest_documents():
    logging.info("Starting document ingestion")
    processor = DocumentProcessor()
    
    with open('./docs/documents_sk_ostprignitz.json', 'r') as f:
        documents = json.load(f)
    
    doc_counter = 0
    for title, url in documents.items():
        try:
            logging.info(f"Processing document [{doc_counter}]: {title}")
            # Download and process document
            local_file = processor.download_document(title, url)
            markdown_content = processor.convert_to_markdown(local_file)
            chunks = processor.split_markdown(markdown_content)
            
            # Store each chunk in Redis
            for i, chunk in enumerate(chunks):
                chunk_id = f'doc:{doc_counter}'
                # Create embeddings synchronously
                chunk_embedding = embeddings.embed_query(chunk.page_content)
                title_embedding = embeddings.embed_query(title)
                final_embedding = [(a + 9 * b) / 10 for a, b in zip(chunk_embedding, title_embedding)]
                doc_data = {
                    'text': chunk.page_content,
                    'title': title,
                    'url': url,
                    'metadata': {'chunk': i, 'source': title},  # Simplified metadata
                    'embedding': final_embedding
                }
                
                redis_client.json().set(chunk_id, '$', doc_data)
                print(f"Indexed chunk {i+1} for document: {title}")
                doc_counter += 1
            logging.info(f"Successfully processed {title} ({len(chunks)} chunks)")
                
        except Exception as e:
            logging.error(f"Error processing document {title}: {str(e)}")
            continue
    
    logging.info(f"Ingestion complete. Processed {doc_counter} total chunks")

if __name__ == "__main__":
    create_index()
    ingest_documents()