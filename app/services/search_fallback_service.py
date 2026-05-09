import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class SearchFallbackService:
    """
    Serviço para melhorar dinâmica de pesquisa com estratégias de fallback.
    Tenta múltiplas estratégias de busca se resultados forem vazios.
    """

    def __init__(self, database_repository: Any = None):
        self.database_repository = database_repository

    def extract_search_terms(self, text: str) -> list[str]:
        """
        Extrai termos de busca da pergunta/texto.
        Separa por palavras-chave, remove stopwords, e retorna em ordem de relevância.
        """
        if not text:
            return []

        # Remove caracteres especiais, mantém alphanumericos e espaços
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())

        # Split em palavras
        words = cleaned.split()

        # Filtra stopwords comuns em português/inglês
        stopwords = {
            "de", "da", "do", "e", "ou", "para", "com", "em", "um", "uma",
            "o", "a", "os", "as", "é", "são", "por", "como", "entre",
            "mais", "menor", "maior", "que", "qual", "onde", "quando",
            "the", "a", "an", "and", "or", "for", "with", "in", "at",
            "to", "is", "are", "from", "by", "on", "about", "what", "how"
        }

        # Mantém palavras com mais de 3 caracteres que não são stopwords
        terms = [w for w in words if len(w) > 3 and w not in stopwords]

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                unique_terms.append(term)
                seen.add(term)

        return unique_terms

    def build_like_conditions(self, field: str, terms: list[str], operator: str = "OR") -> str:
        """
        Constrói condições LIKE múltiplas para um campo.
        Exemplo: "topic LIKE '%python%' OR topic LIKE '%programming%'"
        """
        if not terms:
            return ""

        conditions = [f"LOWER({field}) LIKE LOWER('%{term}%')" for term in terms]
        return f" {operator} ".join(conditions)

    def build_videos_fallback_queries(self, search_terms: list[str], limit: int) -> list[str]:
        """
        Gera múltiplas queries de fallback para tabela videos.
        Tenta ordenação por diferentes critérios de relevância.
        """
        queries = []

        if search_terms:
            # Query 1: Busca no title (mais relevante)
            title_conditions = self.build_like_conditions("title", search_terms, "OR")
            if title_conditions:
                queries.append(
                    f"SELECT id, title, url, topic, difficulty_level FROM videos "
                    f"WHERE {title_conditions} "
                    f"ORDER BY difficulty_level ASC LIMIT {limit}"
                )

            # Query 2: Busca em title + topic
            topic_conditions = self.build_like_conditions("topic", search_terms, "OR")
            if topic_conditions:
                queries.append(
                    f"SELECT id, title, url, topic, difficulty_level FROM videos "
                    f"WHERE {title_conditions} OR {topic_conditions} "
                    f"ORDER BY difficulty_level ASC LIMIT {limit}"
                )

        # Query 3: Fallback genérico - retorna videos de baixa dificuldade
        queries.append(
            f"SELECT id, title, url, topic, difficulty_level FROM videos "
            f"ORDER BY difficulty_level ASC, duration_minutes ASC LIMIT {limit}"
        )

        return queries

    def build_literature_fallback_queries(self, search_terms: list[str], limit: int) -> list[str]:
        """
        Gera múltiplas queries de fallback para tabela literature.
        Tenta ordenação por citações e relevância.
        """
        queries = []

        if search_terms:
            # Query 1: Busca em title
            title_conditions = self.build_like_conditions("title", search_terms, "OR")
            if title_conditions:
                queries.append(
                    f"SELECT id, title, topic, keywords, level FROM literature "
                    f"WHERE {title_conditions} "
                    f"ORDER BY citations DESC, publication_year DESC LIMIT {limit}"
                )

            # Query 2: Busca em keywords (muito relevante para literatura)
            keywords_conditions = self.build_like_conditions("keywords", search_terms, "OR")
            if keywords_conditions:
                queries.append(
                    f"SELECT id, title, topic, keywords, level FROM literature "
                    f"WHERE {keywords_conditions} OR {title_conditions} "
                    f"ORDER BY citations DESC LIMIT {limit}"
                )

            # Query 3: Busca em description
            description_conditions = self.build_like_conditions("description", search_terms, "OR")
            if description_conditions:
                queries.append(
                    f"SELECT id, title, topic, keywords, level FROM literature "
                    f"WHERE {title_conditions} OR {keywords_conditions} OR {description_conditions} "
                    f"ORDER BY citations DESC LIMIT {limit}"
                )

        # Query 4: Fallback - literatura mais citada por nível
        queries.append(
            f"SELECT id, title, topic, keywords, level FROM literature "
            f"ORDER BY citations DESC, publication_year DESC LIMIT {limit}"
        )

        return queries

    def build_disciplines_fallback_queries(self, search_terms: list[str], limit: int) -> list[str]:
        """
        Gera múltiplas queries de fallback para tabela disciplines.
        Tenta ordenação por semestre e dificuldade.
        """
        queries = []

        if search_terms:
            # Query 1: Busca em name
            name_conditions = self.build_like_conditions("name", search_terms, "OR")
            if name_conditions:
                queries.append(
                    f"SELECT id, name, difficulty_level, credits, department FROM disciplines "
                    f"WHERE {name_conditions} "
                    f"ORDER BY semester ASC, difficulty_level ASC LIMIT {limit}"
                )

            # Query 2: Busca em name + acquired_skills
            skills_conditions = self.build_like_conditions("acquired_skills", search_terms, "OR")
            if skills_conditions:
                queries.append(
                    f"SELECT id, name, difficulty_level, credits, department FROM disciplines "
                    f"WHERE {name_conditions} OR {skills_conditions} "
                    f"ORDER BY semester ASC LIMIT {limit}"
                )

            # Query 3: Busca em syllabus + tools_used
            syllabus_conditions = self.build_like_conditions("syllabus", search_terms, "OR")
            tools_conditions = self.build_like_conditions("tools_used", search_terms, "OR")
            if syllabus_conditions or tools_conditions:
                queries.append(
                    f"SELECT id, name, difficulty_level, credits, department FROM disciplines "
                    f"WHERE {name_conditions} OR {syllabus_conditions} OR {tools_conditions} "
                    f"ORDER BY semester ASC LIMIT {limit}"
                )

        # Query 4: Fallback - disciplinas por semestre
        queries.append(
            f"SELECT id, name, difficulty_level, credits, department FROM disciplines "
            f"ORDER BY semester ASC, difficulty_level ASC LIMIT {limit}"
        )

        return queries

    def execute_fallback_queries(self, queries: list[str]) -> list[dict]:
        """
        Executa queries até encontrar resultado não-vazio.
        Retorna primeiro resultado que retornar dados.
        """
        if not self.database_repository:
            return []

        for query in queries:
            try:
                logger.info(f"Tentando query de fallback: {query[:100]}...")
                results = self.database_repository._fetch_rows(query)
                if results:
                    logger.info(f"Fallback query retornou {len(results)} resultados")
                    return results
            except Exception as e:
                logger.debug(f"Fallback query falhou: {e}")
                continue

        logger.warning("Todas as queries de fallback retornaram vazio")
        return []
