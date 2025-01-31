import os
import warnings
import redis
import numpy as np
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.callbacks.tracers import LangChainTracer
from redis.commands.search.query import Query

ollama_host = os.getenv("OLLAMA_HOST", "localhost")
redis_host = os.getenv("REDIS_HOST", "localhost")

load_dotenv()
warnings.filterwarnings("ignore")

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "sparkasse-rag"
load_dotenv('secrets.env')

def get_relevant_documents(query: str, top_k: int = 3):
    """Get relevant documents using Redis vector search"""
    client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=f"http://{ollama_host}:11434")
    
    # Create query embedding
    query_embedding = embeddings.embed_query(query)
    query_vector = np.array(query_embedding).astype(np.float32).tobytes()
    
    # Search Redis
    q = (Query(f"*=>[KNN {top_k} @embedding $vec as score]")
         .sort_by("score")
         .return_fields("text", "title", "url", "score")
         .dialect(2))
    
    results = client.ft("docs").search(q, {"vec": query_vector}).docs
    return results

def create_rag_chain():
    tracer = LangChainTracer(project_name="sparkasse-rag")

    def get_context(query):
        docs = get_relevant_documents(query)
        return "\n\n".join([
            f"Dokumentname: {doc.title}\n"
            f"Link: {doc.url}\n"
            f"Inhalt: {doc.text}"
            for doc in docs
        ])
    
    prompt = """
    Sie sind ein Assistent der Sparkasse und beantworten Fragen mithilfe von Dokumenten der Sparkasse, die Sie als Kontext erhalten. Nutzen Sie den Kontext für genaue Antworten.
    Wenn Sie etwas nicht wissen, sagen Sie es offen. Nennen Sie immer den Dokumentnamen und Link, aus dem Sie die Information haben.
    Antworten Sie in Plaintext, nicht Markdown.

    FRAGE: {question}
    
    KONTEXT: {context}
    
    ANTWORT: 
    """
    model = ChatOllama(model="llama3.2:1b", base_url=f"http://{ollama_host}:11434")
    template = ChatPromptTemplate.from_template(prompt)
    
    return (
        {
            "context": get_context,
            "question": RunnablePassthrough()
        }
        | template
        | model
        | StrOutputParser()
    ).with_config(callbacks=[tracer])

def interactive_mode(rag_chain):
    print("\n" + "=" * 60)
    print("🏦 Willkommen bei Ihrem Sparkassen-Assistenten!")
    print("Ich kann Ihnen Fragen zu Sparkassen-Dokumenten beantworten.")
    print("Sie können jederzeit 'exit' eingeben, um zu beenden.")
    print("=" * 60 + "\n")
    
    while True:
        try:
            question = input("➤ ").strip()
            if question.lower() in ['exit', 'quit', 'q']:
                print("\nAuf Wiedersehen! 👋")
                break
            if not question:
                continue
                
            print("\n", end="", flush=True)
            for token in rag_chain.stream(question):
                print(token, end="", flush=True)
            print("\n\n" + "-" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\nAuf Wiedersehen! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

if __name__ == "__main__":
    # Start chat
    rag_chain = create_rag_chain()
    interactive_mode(rag_chain)