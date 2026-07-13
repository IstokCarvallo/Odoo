from __future__ import annotations

import logging
import sys
from pathlib import Path

from clients.odoo_client import OdooClient
from config.settings import Settings
from extractors.personal_extractor import PersonalExtractor
from repositories.sql_repository import SqlRepository


def configure_logging() -> None:
    """
    Configuración centralizada del logging.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:

    configure_logging()

    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("ETL ODOO → SQL SERVER")
    logger.info("=" * 70)

    try:

        # ---------------------------------------------------------
        # Configuración
        # ---------------------------------------------------------

        settings = Settings()

        # ---------------------------------------------------------
        # Conexión Odoo
        # ---------------------------------------------------------

        logger.info("Conectando a Odoo...")

        client = OdooClient(
            url=settings.odoo_url,
            database=settings.odoo_database,
            username=settings.odoo_username,
            password=settings.odoo_password,
        )

        client.connect()

        logger.info("Conexión Odoo OK.")

        # ---------------------------------------------------------
        # Extracción
        # ---------------------------------------------------------

        extractor = PersonalExtractor(client)

        registros = extractor.extract()

        logger.info(
            "Registros extraídos: %s",
            len(registros)
        )

        # ---------------------------------------------------------
        # SQL Server
        # ---------------------------------------------------------

        repository = SqlRepository(
            settings.sql_connection_string
        )

        repository.save_snapshot(registros)

        logger.info("Proceso finalizado correctamente.")

        return 0

    except Exception:

        logger.exception("Error ejecutando ETL.")

        return 1


if __name__ == "__main__":

    sys.exit(main())