import json
import redis
import requests
from pathlib import Path
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from langchain_ollama import OllamaEmbeddings
from docling.document_converter import DocumentConverter
from langchain_text_splitters import MarkdownHeaderTextSplitter

# Initialize Redis connection
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Initialize embeddings
embeddings = OllamaEmbeddings(model='nomic-embed-text', base_url="http://localhost:11434")
VECTOR_DIM = 384  # Dimension of embeddings

class DocumentProcessor:
    def __init__(self, download_dir="./docs/downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.converter = DocumentConverter()
        
    def download_document(self, title, url):
        extension = url.split('.')[-1].lower()
        local_file = self.download_dir / f"{title}.{extension}"
        
        if not local_file.exists():
            response = requests.get(url)
            with open(local_file, "wb") as f:
                f.write(response.content)
        
        return local_file
    
    def convert_to_markdown(self, file_path):
        result = self.converter.convert(str(file_path))
        return result.document.export_to_markdown()
    
    def split_markdown(self, markdown_content):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3")
        ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
        return splitter.split_text(markdown_content)

def create_index():
    # Create Redis search index
    try:
        redis_client.ft('docs').dropindex()
    except:
        pass

    schema = (
        TextField("$.text", as_name="text"),
        TextField("$.title", as_name="title"),
        TextField("$.url", as_name="url"),
        VectorField("$.embedding", 
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

def ingest_documents():
    processor = DocumentProcessor()
    
    with open('./docs/documents_sk_ostprignitz.json', 'r') as f:
        documents = json.load(f)
    
    doc_counter = 0
    for title, url in documents.items():
        try:
            # Download and process document
            local_file = processor.download_document(title, url)
            markdown_content = processor.convert_to_markdown(local_file)
            chunks = processor.split_markdown(markdown_content)
            
            # Store each chunk in Redis
            for i, chunk in enumerate(chunks):
                chunk_id = f'doc:{doc_counter}'
                doc_data = {
                    'text': chunk.page_content,
                    'title': title,
                    'url': url,
                    'metadata': chunk.metadata,
                    'embedding': embeddings.embed_query(chunk.page_content)
                }
                
                redis_client.json().set(chunk_id, '$', doc_data)
                print(f"Indexed chunk {i+1} for document: {title}")
                doc_counter += 1
                
        except Exception as e:
            print(f"Error processing document {title}: {str(e)}")
            continue

if __name__ == "__main__":
    create_index()
    ingest_documents()