import os
from langchain_core.documents import Document
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Conecta ao banco de dados MySQL usando credenciais do env."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
        )
    except mysql.connector.Error as e:
        raise ConnectionError(f"Erro ao conectar no banco de dados MySQL: {e}")
    except ValueError as e:
        raise ValueError(f"Configuração inválida do banco de dados: {e}")


def test_db_connection() -> bool:
    """Testa se consegue conectar ao banco de dados."""
    try:
        connection = get_db_connection()
        connection.close()
        return True
    except Exception as e:
        raise ConnectionError(f"Falha na conexão com o banco de dados: {str(e)}")


def load_videos() -> list[Document]:
    """Carrega dados da tabela videos."""
    documents = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM videos")
        
        for row in cursor.fetchall():
            content = f"""
Título: {row.get('title', '')}
Plataforma: {row.get('platform', '')}
Duração: {row.get('duration_minutes', '')} minutos
Tópico: {row.get('topic', '')}
Idioma: {row.get('language', '')}
Nível de Dificuldade: {row.get('difficulty_level', '')}
Fonte: {row.get('source', '')}
URL: {row.get('url', '')}
            """.strip()
            
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": "videos",
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "type": "video"
                }
            ))
        
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Erro ao carregar vídeos: {e}")
    
    return documents


def load_literature() -> list[Document]:
    """Carrega dados da tabela literature."""
    documents = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM literature")
        
        for row in cursor.fetchall():
            content = f"""
Título: {row.get('title', '')}
Tipo: {row.get('type', '')}
Tópico: {row.get('topic', '')}
Autores: {row.get('authors', '')}
Ano de Publicação: {row.get('publication_year', '')}
Idioma: {row.get('language', '')}
Nível: {row.get('level', '')}
Acesso: {row.get('access', '')}
Formato: {row.get('format', '')}
Descrição: {row.get('description', '')}
Palavras-chave: {row.get('keywords', '')}
Instituição: {row.get('institution', '')}
URL: {row.get('url', '')}
            """.strip()
            
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": "literature",
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "type": row.get("type")
                }
            ))
        
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Erro ao carregar literatura: {e}")
    
    return documents


def load_disciplines() -> list[Document]:
    """Carrega dados da tabela disciplines."""
    documents = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM disciplines")
        
        for row in cursor.fetchall():
            content = f"""
Nome da Disciplina: {row.get('name', '')}
Ementa: {row.get('syllabus', '')}
Pré-requisitos: {row.get('prerequisites', '')}
Carga Horária: {row.get('workload_hours', '')} horas
Semestre: {row.get('semester', '')}
Nível de Dificuldade: {row.get('difficulty_level', '')}
Departamento: {row.get('department', '')}
Créditos: {row.get('credits', '')}
Habilidades Adquiridas: {row.get('acquired_skills', '')}
Ferramentas Utilizadas: {row.get('tools_used', '')}
Métodos de Avaliação: {row.get('assessment_methods', '')}
            """.strip()
            
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": "disciplines",
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "type": "disciplina"
                }
            ))
        
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Erro ao carregar disciplinas: {e}")
    
    return documents


def load_all_db_documents() -> list[Document]:
    """Carrega todos os documentos do banco de dados."""
    try:
        # Testa conexão primeiro
        test_db_connection()
    except ConnectionError as e:
        raise ConnectionError(str(e))
    
    all_documents = []
    try:
        all_documents.extend(load_videos())
        all_documents.extend(load_literature())
        all_documents.extend(load_disciplines())
    except Exception as e:
        raise Exception(f"Erro ao carregar documentos do banco: {str(e)}")
    
    if not all_documents:
        raise ValueError("Nenhum documento encontrado no banco de dados")
    
    return all_documents
