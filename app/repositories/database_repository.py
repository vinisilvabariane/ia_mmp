import logging
import os
import re
from collections.abc import Iterable

import mysql.connector
from dotenv import load_dotenv

from app.core.config import DB_CONNECT_TIMEOUT_SECONDS
from app.core.errors import DependencyAppError, SQLExecutionError

load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseRepository:
    ALLOWED_TABLES = {"videos", "literature", "disciplines"}
    FORBIDDEN_SQL_PATTERNS = (
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bDROP\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bCALL\b",
        r"\bEXEC\b",
    )

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "3306")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                database=os.getenv("DB_NAME"),
                connection_timeout=DB_CONNECT_TIMEOUT_SECONDS,
            )
        except mysql.connector.Error as exc:
            raise DependencyAppError(f"Erro ao conectar no banco de dados MySQL: {exc}") from exc
        except ValueError as exc:
            raise DependencyAppError(f"Configuracao invalida do banco de dados: {exc}") from exc

    def test_connection(self) -> bool:
        try:
            connection = self.get_connection()
            connection.close()
            return True
        except Exception as exc:
            raise DependencyAppError(f"Falha na conexao com o banco de dados: {exc}") from exc

    def readiness(self) -> dict[str, bool]:
        database_ready = False
        try:
            database_ready = self.test_connection()
        except DependencyAppError:
            logger.warning("database_readiness_check_failed")

        return {
            "database": database_ready,
            "db_host_configured": bool(os.getenv("DB_HOST")),
            "db_name_configured": bool(os.getenv("DB_NAME")),
        }

    def execute_resource_queries(self, queries: dict[str, str | None], limit: int) -> dict[str, list[dict]]:
        connection = None
        results: dict[str, list[dict]] = {}
        try:
            connection = self.get_connection()
            for key, query in queries.items():
                if not query:
                    results[key] = []
                    logger.debug("Query %s e None/vazia, retornando lista vazia", key)
                    continue
                try:
                    sanitized_query = self._sanitize_select_query(query=query, limit=limit)
                    logger.info("executing_resource_query key=%s", key)
                    logger.debug("Sanitized query: %s...", sanitized_query[:200])
                    rows = self._fetch_rows(sanitized_query, connection=connection)
                    results[key] = rows
                    logger.info("resource_query_success key=%s rows=%s", key, len(rows))
                except Exception as exc:
                    logger.error("resource_query_failed key=%s error=%s", key, exc)
                    results[key] = []

            return results
        finally:
            if connection is not None:
                connection.close()

    def _fetch_rows(
        self,
        query: str,
        params: Iterable | None = None,
        *,
        connection: mysql.connector.MySQLConnection | None = None,
    ) -> list[dict]:
        managed_connection = connection is None
        active_connection = connection
        cursor = None
        try:
            if active_connection is None:
                active_connection = self.get_connection()
            cursor = active_connection.cursor(dictionary=True)
            logger.debug("Executando query: %s...", query[:150])
            cursor.execute(query, params or ())
            rows = list(cursor.fetchall())
            logger.debug("Query retornou %s linhas", len(rows))
            return rows
        except mysql.connector.Error as exc:
            logger.error("MySQL error ao executar query: %s", exc)
            raise SQLExecutionError(f"Falha ao executar query SQL: {exc}") from exc
        finally:
            if cursor is not None:
                cursor.close()
            if managed_connection and active_connection is not None:
                active_connection.close()

    def _sanitize_select_query(self, query: str, limit: int) -> str:
        cleaned_query = query.strip().strip("`").strip()
        cleaned_query = re.sub(r"^sql\s+", "", cleaned_query, flags=re.IGNORECASE)
        cleaned_query = cleaned_query.rstrip(";").strip()

        if not cleaned_query:
            raise ValueError("Query SQL vazia")

        if ";" in cleaned_query:
            raise ValueError("Apenas uma query SQL por vez e permitida")

        if not re.match(r"^\s*SELECT\b", cleaned_query, flags=re.IGNORECASE):
            raise ValueError("Apenas queries SELECT sao permitidas")

        for pattern in self.FORBIDDEN_SQL_PATTERNS:
            if re.search(pattern, cleaned_query, flags=re.IGNORECASE):
                raise ValueError("A query SQL contem comandos nao permitidos")

        table_names = {
            match.lower()
            for match in re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", cleaned_query, flags=re.IGNORECASE)
        }
        if not table_names:
            logger.warning("Nenhuma tabela encontrada na query: %s", cleaned_query[:100])
            raise ValueError("A query SQL precisa referenciar ao menos uma tabela permitida")

        invalid_tables = table_names - self.ALLOWED_TABLES
        if invalid_tables:
            raise ValueError(f"Tabelas nao permitidas na query SQL: {', '.join(sorted(invalid_tables))}")

        if not re.search(r"\bLIMIT\s+\d+\b", cleaned_query, flags=re.IGNORECASE):
            logger.debug("Adicionando LIMIT %s a query", limit)
            cleaned_query = f"{cleaned_query} LIMIT {limit}"

        logger.debug("Query sanitizada com sucesso: %s...", cleaned_query[:150])
        return cleaned_query
