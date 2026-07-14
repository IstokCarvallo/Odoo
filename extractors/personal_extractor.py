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
    

    def _load_contracts(self, limit: int | None = None,) -> list[dict]:
        """
        Obtiene los contratos desde Odoo.
        """

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

        return self._client.execute(
            "hr.contract",
            "search_read",
            [[("state", "in", ["open", "close"])]],
            kwargs,
        )


    def _collect_ids(self, contracts: list[dict], ) -> dict[str, set[int]]:
        """
        Recolecta todos los IDs relacionados presentes en los contratos.
        """

        employee_ids: set[int] = set()
        department_ids: set[int] = set()
        company_ids: set[int] = set()
        calendar_ids: set[int] = set()

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

        return {
            "employee_ids": employee_ids,
            "department_ids": department_ids,
            "company_ids": company_ids,
            "calendar_ids": calendar_ids,
        }
    

    def _load_catalog(self,
                model: str,
                ids: set[int],
                fields: list[str],) -> dict[int, dict]:
        """
        Carga un catálogo desde Odoo y lo devuelve indexado por Id.
        """

        if not ids:
            return {}

        data = self._client.execute(
            model,
            "search_read",
            [[("id", "in", list(ids))]],
            {
                "fields": fields,
            },
        )

        return {
            row["id"]: row
            for row in data
        }
    

    def _build_row(
            self,
            contract: dict,
            employees: dict[int, dict],
            departments: dict[int, dict],
            companies: dict[int, dict],
            parent_companies: dict[int, dict],
            jobs: dict[int, dict],
            calendars: dict[int, dict],
        ) -> StgOdooContrato:
            """
            Construye un registro de staging a partir de un contrato.
            """

            employee = (
                employees.get(contract["employee_id"][0], {})
                if contract.get("employee_id")
                else {}
            )

            department = (
                departments.get(contract["department_id"][0], {})
                if contract.get("department_id")
                else {}
            )

            company = (
                companies.get(contract["company_id"][0], {})
                if contract.get("company_id")
                else {}
            )

            parent_company = {}

            if company.get("parent_id"):
                parent_company = parent_companies.get(
                    company["parent_id"][0],
                    {}
                )

            calendar = {}

            if contract.get("resource_calendar_id"):
                calendar = calendars.get(
                    contract["resource_calendar_id"][0],
                    {}
                )

            job = {}

            if employee.get("job_id"):
                job = jobs.get(
                    employee["job_id"][0],
                    {}
                )

            return StgOdooContrato(
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
                EmpleadoId=employee.get("id"),

                Rut=self._value(employee.get("identification_id")),

                PrimerNombre=self._value(employee.get("firstname")),
                SegundoNombre=self._value(employee.get("middle_name")),

                ApellidoPaterno=self._value(employee.get("last_name")),
                ApellidoMaterno=self._value(employee.get("mothers_name")),

                # ---------------------------------------------
                # Departamento
                # ---------------------------------------------
                DepartamentoId=department.get("id"),
                Departamento=department.get("name"),

                # ---------------------------------------------
                # Empresa
                # ---------------------------------------------
                EmpresaId=company.get("id"),
                Empresa=company.get("name"),

                EmpresaPadreId=parent_company.get("id"),
                EmpresaPadre=parent_company.get("name"),

                # ---------------------------------------------
                # Calendario
                # ---------------------------------------------
                CalendarioId=calendar.get("id"),
                Calendario=calendar.get("name"),

                # -------------------------------------------------
                # Centro de costo
                # (Pendiente de identificar el modelo en Odoo)
                # -------------------------------------------------
                CentroCostoId=None,
                CentroCosto=None,

                # -------------------------------------------------
                # Cargo
                # -------------------------------------------------
                CargoId=job.get("id"),
                Cargo=job.get("name"),

                # -------------------------------------------------
                # Metadatos ETL
                # -------------------------------------------------
                FechaExtraccion=self._context.started_at,
                ExecutionId=self._context.execution_id,
            )
    

    def extract(self, limit: int | None = None) -> tuple[list[StgOdooContrato], UUID]:
        
        contracts = self._load_contracts(limit)
        ids = self._collect_ids(contracts)

        employee_ids = ids["employee_ids"]
        department_ids = ids["department_ids"]
        company_ids = ids["company_ids"]
        calendar_ids = ids["calendar_ids"]

        parent_company_ids: set[int] = set()
        job_ids: set[int] = set()

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
        employees = self._load_catalog("hr.employee", employee_ids,
            [
                "id",
                "identification_id",
                "firstname",
                "middle_name",
                "last_name",
                "mothers_name",
                "company_id",
                "department_id",
                "job_id",
            ],
        )

        for employee in employees.values():
            company = employee.get("company_id")

            if company:
                company_ids.add(company[0])

            department = employee.get("department_id")

            if department:
                department_ids.add(department[0])

            job = employee.get("job_id")

            if job:
                job_ids.add(job[0])

        # -------------------------------------------------------------
        # Cargos
        # -------------------------------------------------------------
        jobs = self._load_catalog("hr.job", job_ids,
            [
                "id",
                "name",
            ],
        )
        
        # -------------------------------------------------------------
        # Departamentos
        # -------------------------------------------------------------
        departments = self._load_catalog("hr.department", department_ids,
            [
                "id",
                "name",
                "company_id",
            ],
        )

        for department in departments.values():
            company = department.get("company_id")

            if company:
                company_ids.add(company[0])

        # -------------------------------------------------------------
        # Empresas
        # -------------------------------------------------------------
        companies = self._load_catalog("res.company", company_ids,
            [
                "id",
                "name",
                "parent_id",
            ],
        )

        for company in companies.values():
            parent = company.get("parent_id")

            if parent:
                parent_company_ids.add(parent[0])

        # -------------------------------------------------------------
        # Compañías padre
        # -------------------------------------------------------------
        parent_companies = self._load_catalog("res.company", parent_company_ids,
            [
                "id",
                "name",
            ],
        )

        # -------------------------------------------------------------
        # Calendarios
        # -------------------------------------------------------------
        calendars = self._load_catalog("resource.calendar", calendar_ids,
            [
                "id",
                "name",
            ],
        )

        # -------------------------------------------------------------
        # Construcción del modelo STG
        # -------------------------------------------------------------

        registros: list[StgOdooContrato] = []

        for contract in contracts:
            registros.append(
                self._build_row(
                    contract,
                    employees,
                    departments,
                    companies,
                    parent_companies,
                    jobs,
                    calendars,
                )
            )

        return registros