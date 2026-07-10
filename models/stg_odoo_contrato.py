from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class StgOdooContrato:
    """
    Representa una fila de la tabla STG_OdooContrato.

    Esta clase es el contrato entre el extractor de Odoo y el repositorio
    encargado de persistir la información en SQL Server.
    """

    # ------------------------------------------------------------------
    # Contrato
    # ------------------------------------------------------------------

    ContratoId: int
    NombreContrato: str
    Estado: str

    FechaInicio: date | None
    FechaTermino: date | None

    # ------------------------------------------------------------------
    # Empleado
    # ------------------------------------------------------------------

    EmpleadoId: int

    Rut: str | None

    PrimerNombre: str | None
    SegundoNombre: str | None

    ApellidoPaterno: str | None
    ApellidoMaterno: str | None

    # ------------------------------------------------------------------
    # Departamento
    # ------------------------------------------------------------------

    DepartamentoId: int | None
    Departamento: str | None

    # ------------------------------------------------------------------
    # Empresa
    # ------------------------------------------------------------------

    EmpresaId: int
    Empresa: str

    EmpresaPadreId: int | None
    EmpresaPadre: str | None

    # ------------------------------------------------------------------
    # Calendario
    # ------------------------------------------------------------------

    CalendarioId: int | None
    Calendario: str | None

    # ------------------------------------------------------------------
    # Centro de costo
    # (pendiente de descubrir en Odoo)
    # ------------------------------------------------------------------

    CentroCostoId: int | None = None
    CentroCosto: str | None = None

    # ------------------------------------------------------------------
    # ETL
    # ------------------------------------------------------------------

    FechaExtraccion: datetime | None = None

    ExecutionId: UUID | None = None