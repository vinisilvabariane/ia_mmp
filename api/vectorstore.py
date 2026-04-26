from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

from config import EMBEDDINGS_MODEL, QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT


class SentenceTransformerEmbeddings(Embeddings):
    """Wrapper para SentenceTransformer que elimina avisos de arquitetura."""
    
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed search docs."""
        return self.model.encode(texts, normalize_embeddings=True).tolist()
    
    def embed_query(self, text: str) -> list[float]:
        """Embed query text."""
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()


@lru_cache(maxsize=1)
def get_embeddings() -> SentenceTransformerEmbeddings:
    return SentenceTransformerEmbeddings(
        model_name=EMBEDDINGS_MODEL,
        device="cpu",
    )


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


class VectorStoreManager:
    def __init__(self, collection_name: str = QDRANT_COLLECTION):
        self.collection_name = collection_name

    def load(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=get_qdrant_client(),
            collection_name=self.collection_name,
            embedding=get_embeddings(),
        )

    def recreate(self, documents: list) -> QdrantVectorStore:
        client = get_qdrant_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass

        return QdrantVectorStore.from_documents(
            documents=documents,
            embedding=get_embeddings(),
            url=f"http://{QDRANT_HOST}:{QDRANT_PORT}",
            collection_name=self.collection_name,
        )
