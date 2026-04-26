from pathlib import Path

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR, SUPPORTED_EXTENSIONS
from db_loader import load_all_db_documents
from vectorstore import VectorStoreManager


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_file(path: Path) -> list[Document]:
    suffix = path.suffix.lower()

    if suffix == ".txt":
        content = _read_text_file(path)
    elif suffix == ".csv":
        content = pd.read_csv(path).to_csv(index=False)
    elif suffix in {".xlsx", ".xls"}:
        content = pd.read_excel(path).to_csv(index=False)
    else:
        return []

    return [Document(page_content=str(content), metadata={"source": path.name})]


def load_documents(data_dir: Path) -> list[Document]:
    documents = []
    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.extend(_load_file(path))
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )
    return splitter.split_documents(documents)


def run_ingest() -> dict:
    # Carrega documentos do banco de dados
    documents = load_all_db_documents()
    
    # Split de documentos
    chunks = split_documents(documents)
    VectorStoreManager().recreate(chunks)

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "collection": VectorStoreManager().collection_name,
        "database_docs": len(documents),
        "file_docs": 0,
    }


if __name__ == "__main__":
    print(run_ingest())
