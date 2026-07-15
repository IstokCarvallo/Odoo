from __future__ import annotations

import logging
import sys
from pathlib import Path
from datetime import datetime

from clients.odoo_client import OdooClient
from config import settings
from config.settings import Settings
from extractors.personal_extractor import PersonalExtractor
from repositories.sql_repository import SqlRepository
from context.execution_context import ExecutionContext

# from tools.discover_models import discover_models
# from tools.discover_model import DiscoverModel

def configure_logging(context: ExecutionContext) -> logging.Logger:
    """
    Configura el logger de la aplicación.

    Crea un archivo de log independiente por ejecución.
    """

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_name = context.started_at.strftime("etl_%Y%m%d_%H%M%S.log")
    log_file = log_dir / log_name

    context.log_file = log_file

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        "%Y-%m-%d %H:%M:%S")

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)

    # Consola
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # Archivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)

    logger.info("Log de ejecución: %s", log_file)

    return logger


def main() -> int:
    context = ExecutionContext()
    configure_logging(context)

    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("ETL ODOO → SQL SERVER")
    logger.info("ExecutionId : %s", context.execution_id)
    logger.info("Inicio      : %s", context.started_at)
    logger.info("Log         : %s", context.log_file)
    logger.info("=" * 70)

    try:
        settings = Settings()

        logger.info("Conectando a Odoo...")
        client = OdooClient(settings.odoo)

        client.connect()
        logger.info("Conexión Odoo OK.")

        # ---------------------------------------------------------
        # Extracción
        # ---------------------------------------------------------

        extractor = PersonalExtractor(client, context)
        registros = extractor.extract()
        logger.info("Registros extraídos: %s", len(registros))

        # ---------------------------------------------------------
        # SQL Server
        # ---------------------------------------------------------

        repository = SqlRepository(settings.sql_connection_string, context)
        repository.save_snapshot(registros)

        logger.info("Proceso finalizado correctamente.")
        return 0

    except Exception:
        logger.exception("Error ejecutando ETL.")
        return 1


if __name__ == "__main__":
    # settings = Settings()
    # client = OdooClient(settings.odoo)
    # client.connect()
    # #discover_models(client)
    # tool = DiscoverModel(client)
    # tool.inspect("res.company")
    sys.exit(main())