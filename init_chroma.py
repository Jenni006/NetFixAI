import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import EmbeddingFunction

embedder = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    collection = chroma_client.get_collection("netfix")
    print("Collection 'netfix' already exists!")
except:
    def embedding_fn(texts):
        return embedder.encode(texts, convert_to_numpy=True).tolist()

    embedding_function = EmbeddingFunction(embedding_fn)
    
    collection = chroma_client.create_collection(
        name="netfix",
        embedding_function=embedding_function
    )
    print("Collection 'netfix' created!")