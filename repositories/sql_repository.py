from __future__ import annotations

import logging
import pyodbc

from models import StgOdooContrato

logger = logging.getLogger(__name__)


class SqlRepository:
    """
    Repositorio encargado de persistir la tabla STG_OdooContrato.

    Responsabilidades:
        - Abrir conexión SQL Server.
        - Iniciar transacción.
        - Limpiar la tabla staging.
        - Insertar los registros.
        - Confirmar o revertir la transacción.

    No contiene reglas de negocio.
    """

    INSERT_SQL = """
    INSERT INTO dbo.STG_OdooContrato
    (
        ContratoId,
        NombreContrato,
        Estado,
        FechaInicio,
        FechaTermino,
        EmpleadoId,
        Rut,
        PrimerNombre,
        SegundoNombre,
        ApellidoPaterno,
        ApellidoMaterno,
        DepartamentoId,
        Departamento,
        EmpresaId,
        Empresa,
        EmpresaPadreId,
        EmpresaPadre,
        CalendarioId,
        Calendario,
        CentroCostoId,
        CentroCosto,
        FechaExtraccion,
        ExecutionId,
        HashRegistro
    )
    VALUES
    (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )
    """

    def __init__(self, connection_string: str):

        self._connection_string = connection_string

    def save_snapshot(
        self,
        registros: list[StgOdooContrato]
    ) -> None:

        if not registros:

            logger.warning("No existen registros para cargar.")

            return

        logger.info(
            "Iniciando carga Snapshot (%s registros)...",
            len(registros)
        )

        connection = pyodbc.connect(self._connection_string)

        try:

            cursor = connection.cursor()

            cursor.fast_executemany = True

            logger.info("Iniciando transacción...")

            connection.autocommit = False

            logger.info("Limpiando STG_OdooContrato...")

            cursor.execute(
                "TRUNCATE TABLE dbo.STG_OdooContrato"
            )

            rows = [

                (

                    r.ContratoId,
                    r.NombreContrato,
                    r.Estado,

                    r.FechaInicio,
                    r.FechaTermino,

                    r.EmpleadoId,
                    r.Rut,

                    r.PrimerNombre,
                    r.SegundoNombre,

                    r.ApellidoPaterno,
                    r.ApellidoMaterno,

                    r.DepartamentoId,
                    r.Departamento,

                    r.EmpresaId,
                    r.Empresa,

                    r.EmpresaPadreId,
                    r.EmpresaPadre,

                    r.CalendarioId,
                    r.Calendario,

                    r.CentroCostoId,
                    r.CentroCosto,

                    r.FechaExtraccion,

                    str(r.ExecutionId),

                    r.HashRegistro,

                )

                for r in registros

            ]

            logger.info(
                "Insertando registros..."
            )

            cursor.executemany(
                self.INSERT_SQL,
                rows
            )

            connection.commit()

            logger.info(
                "Carga Snapshot finalizada correctamente."
            )

        except Exception:

            logger.exception(
                "Error durante la carga Snapshot."
            )

            connection.rollback()

            raise

        finally:

            connection.close()