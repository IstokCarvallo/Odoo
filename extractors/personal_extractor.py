"""
PersonalExtractor

Responsabilidad
---------------
Extraer los contratos vigentes desde Odoo y transformarlos en una colección
de objetos StgOdooContrato.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from clients.odoo_client import OdooClient
from models import StgOdooContrato
from context.execution_context import ExecutionContext


class PersonalExtractor:
    def __init__(self, client: OdooClient, context: ExecutionContext):
        self._client = client
        self._context = context


    @staticmethod
    def _value(value):
        if value is False:
            return None

        if value == "":
            return None

        return value
    
    
    @staticmethod
    def _date(value):
        if value is False:
            return None

        if value == "":
            return None

        return value
    

    def extract(self, limit: int | None = None) -> tuple[list[StgOdooContrato], UUID]:
        execution_id = uuid4()
        fecha_extraccion = self._context.started_at
    
        # -------------------------------------------------------------
        # Obtener contratos
        # -------------------------------------------------------------

        kwargs = {
            "fields": [
                "id",
                "name",
                "state",
                "employee_id",
                "department_id",
                "company_id",
                "resource_calendar_id",
                "date_start",
                "date_end",
            ],
            "order": "id desc",
        }

        if limit is not None:
            kwargs["limit"] = limit

        contracts = self._client.execute(
            "hr.contract",
            "search_read",
            [[("state", "in", ["open", "close"])]],
            kwargs,
        )

        if not contracts:
            return [], execution_id 

        # -------------------------------------------------------------
        # Colecciones de IDs relacionados
        # -------------------------------------------------------------

        employee_ids: set[int] = set()
        department_ids: set[int] = set()
        company_ids: set[int] = set()
        calendar_ids: set[int] = set()
        parent_company_ids: set[int] = set()

        for contract in contracts:

            employee = contract.get("employee_id")

            if employee:
                employee_ids.add(employee[0])

            department = contract.get("department_id")

            if department:
                department_ids.add(department[0])

            company = contract.get("company_id")

            if company:
                company_ids.add(company[0])

            calendar = contract.get("resource_calendar_id")

            if calendar:
                calendar_ids.add(calendar[0])

        # -------------------------------------------------------------
        # Empleados
        # -------------------------------------------------------------

        employees: dict[int, dict] = {}

        if employee_ids:

            employee_data = self._client.execute(
                "hr.employee",
                "search_read",
                [[("id", "in", list(employee_ids))]],
                {
                    "fields": [
                        "id",
                        "identification_id",
                        "firstname",
                        "middle_name",
                        "last_name",
                        "mothers_name",
                        "company_id",
                        "department_id",
                    ]
                },
            )

            employees = {
                employee["id"]: employee
                for employee in employee_data
            }

            for employee in employee_data:

                company = employee.get("company_id")

                if company:
                    company_ids.add(company[0])

                department = employee.get("department_id")

                if department:
                    department_ids.add(department[0])

        # -------------------------------------------------------------
        # Departamentos
        # -------------------------------------------------------------

        departments: dict[int, dict] = {}

        if department_ids:

            department_data = self._client.execute(
                "hr.department",
                "search_read",
                [[("id", "in", list(department_ids))]],
                {
                    "fields": [
                        "id",
                        "name",
                        "company_id",
                    ]
                },
            )

            departments = {
                department["id"]: department
                for department in department_data
            }

            for department in department_data:

                company = department.get("company_id")

                if company:
                    company_ids.add(company[0])

        # -------------------------------------------------------------
        # Empresas
        # -------------------------------------------------------------

        companies: dict[int, dict] = {}

        if company_ids:
            company_data = self._client.execute(
                "res.company",
                "search_read",
                [[("id", "in", list(company_ids))]],
                {
                    "fields": [
                        "id",
                        "name",
                        "parent_id",
                    ]
                },
            )

            companies = {
                company["id"]: company
                for company in company_data
            }

            for company in company_data:
                parent = company.get("parent_id")

                if parent:
                    parent_company_ids.add(parent[0])

        # -------------------------------------------------------------
        # Compañías padre
        # -------------------------------------------------------------

        if parent_company_ids:
            parent_data = self._client.execute(
                "res.company",
                "search_read",
                [[("id", "in", list(parent_company_ids))]],
                {
                    "fields": [
                        "id",
                        "name",
                    ]
                },
            )

            for company in parent_data:
                companies[company["id"]] = company

        # -------------------------------------------------------------
        # Calendarios
        # -------------------------------------------------------------

        calendars: dict[int, dict] = {}

        if calendar_ids:
            calendar_data = self._client.execute(
                "resource.calendar",
                "search_read",
                [[("id", "in", list(calendar_ids))]],
                {
                    "fields": [
                        "id",
                        "name",
                    ]
                },
            )

            calendars = {
                calendar["id"]: calendar
                for calendar in calendar_data
            }

        # -------------------------------------------------------------
        # Construcción del modelo STG
        # -------------------------------------------------------------

        registros: list[StgOdooContrato] = []

        for contract in contracts:
            # ---------------------------------------------------------
            # Empleado
            # ---------------------------------------------------------

            employee_id = (
                contract["employee_id"][0]
                if contract.get("employee_id")
                else None
            )

            employee = employees.get(employee_id, {})

            # ---------------------------------------------------------
            # Departamento del contrato
            # ---------------------------------------------------------

            department_id = (
                contract["department_id"][0]
                if contract.get("department_id")
                else None
            )

            department = departments.get(department_id, {})

            # ---------------------------------------------------------
            # Empresa del contrato
            # ---------------------------------------------------------

            company_id = (
                contract["company_id"][0]
                if contract.get("company_id")
                else None
            )

            company = companies.get(company_id, {})

            # ---------------------------------------------------------
            # Empresa padre
            # ---------------------------------------------------------

            parent_company_id = None

            if company.get("parent_id"):
                parent_company_id = company["parent_id"][0]

            parent_company = companies.get(parent_company_id, {})

            # ---------------------------------------------------------
            # Calendario
            # ---------------------------------------------------------

            calendar_id = (
                contract["resource_calendar_id"][0]
                if contract.get("resource_calendar_id")
                else None
            )

            calendar = calendars.get(calendar_id, {})

            # ---------------------------------------------------------
            # Construcción del registro
            # ---------------------------------------------------------

            registro = StgOdooContrato(

                # ---------------------------------------------
                # Contrato
                # ---------------------------------------------
                ContratoId=contract["id"],
                NombreContrato=contract.get("name"),
                Estado=contract.get("state"),

                FechaInicio=self._date(contract.get("date_start")),
                FechaTermino=self._date(contract.get("date_end")),

                # ---------------------------------------------
                # Empleado
                # ---------------------------------------------
                EmpleadoId=employee_id,

                Rut=self._value(employee.get("identification_id")),

                PrimerNombre=self._value(employee.get("firstname")),
                SegundoNombre=self._value(employee.get("middle_name")),

                ApellidoPaterno=self._value(employee.get("last_name")),
                ApellidoMaterno=self._value(employee.get("mothers_name")),

                # ---------------------------------------------
                # Departamento
                # ---------------------------------------------
                DepartamentoId=department_id,
                Departamento=department.get("name"),

                # ---------------------------------------------
                # Empresa
                # ---------------------------------------------
                EmpresaId=company_id,
                Empresa=company.get("name"),

                EmpresaPadreId=parent_company_id,
                EmpresaPadre=parent_company.get("name"),

                # ---------------------------------------------
                # Calendario
                # ---------------------------------------------
                CalendarioId=calendar_id,
                Calendario=calendar.get("name"),

                # -------------------------------------------------
                # Centro de costo
                # (Pendiente de identificar el modelo en Odoo)
                # -------------------------------------------------
                CentroCostoId=None,
                CentroCosto=None,

                # -------------------------------------------------
                # Metadatos ETL
                # -------------------------------------------------
                FechaExtraccion=fecha_extraccion,
                ExecutionId=execution_id,
            )
            registros.append(registro)

        return registros