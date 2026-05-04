import os
import glob
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

# Initialize ChromaDB
DB_DIR = os.path.join(os.path.dirname(__file__), ".chroma_db")
DOCS_DIR = os.path.join(os.path.dirname(__file__), "chocomi_docs")

client = PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(name="chocomi_hardware")

# Initialize Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

def index_documents():
    """Reads all docs from chocomi_docs and indexes them in Chroma."""
    doc_files = glob.glob(os.path.join(DOCS_DIR, "*.txt"))
    if not doc_files:
        print("No documents found in", DOCS_DIR)
        return
        
    docs = []
    ids = []
    metadatas = []
    
    for file_path in doc_files:
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            docs.append(content)
            ids.append(filename) # Use filename as ID for easier evaluation
            metadatas.append({"filename": filename})
            
    print(f"Embedding and indexing {len(docs)} documents...")
    embeddings = model.encode(docs).tolist()
    
    # Clear existing collection and add new
    if collection.count() > 0:
        collection.delete(ids=collection.get()["ids"])
        
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=docs,
        metadatas=metadatas
    )
    print("Indexing complete.")

def retrieve_context(query: str, k: int = 3, return_ids: bool = False) -> str | tuple[str, list[str]]:
    """Retrieves top-k documents for a query."""
    if collection.count() == 0:
        return "" if not return_ids else ("", [])
        
    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k
    )
    
    if not results or not results["documents"] or not results["documents"][0]:
        return "" if not return_ids else ("", [])
        
    retrieved_docs = results["documents"][0]
    retrieved_ids = results["ids"][0]
    
    context = "\n\n---\n\n".join(retrieved_docs)
    if return_ids:
        return context, retrieved_ids
    return context

if __name__ == "__main__":
    index_documents()
