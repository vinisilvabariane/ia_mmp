from langchain_core.documents import Document

from config import RETRIEVER_K
from vectorstore import VectorStoreManager


def build_retriever(k: int = RETRIEVER_K):
    store = VectorStoreManager().load()
    return store.as_retriever(search_kwargs={"k": k})


def format_documents(documents: list[Document]) -> str:
    if not documents:
        return "Nenhum contexto relevante encontrado."

    parts = []
    for document in documents:
        source = document.metadata.get("source", "desconhecido")
        content = document.page_content.strip()
        if not content:
            continue
        parts.append(f"Arquivo: {source}\n{content}")

    return "\n\n---\n\n".join(parts) if parts else "Nenhum contexto relevante encontrado."
