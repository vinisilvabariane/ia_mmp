import logging
import os
from pathlib import Path


def setup_logging(level: str = "INFO") -> None:
    """
    Configura logging com saída para:
    1. Console (stdout)
    2. Arquivo de log em logs/app.log
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Formato de log detalhado
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Handler para console (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configurar root logger
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Log inicial
    root_logger.info(f"Logging iniciado. Arquivo de log: {log_file.absolute()}")
