import json
from pathlib import Path


class Settings:
    """
    Carga la configuración del proyecto desde settings.json y expone
    propiedades tipadas para el resto de la aplicación.
    """

    def __init__(self):
        config_path = (
            Path(__file__)
            .resolve()
            .parent
            / "settings.json"
        )

        if not config_path.exists():
            raise FileNotFoundError(
                f"No existe el archivo de configuración: {config_path}"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

    # ---------------------------------------------------------
    # Configuración completa
    # ---------------------------------------------------------

    @property
    def odoo(self) -> dict:
        return self._config["odoo"]

    @property
    def sqlserver(self) -> dict:
        return self._config["sqlserver"]


    # ---------------------------------------------------------
    # SQL Server
    # ---------------------------------------------------------

    @property
    def sql_connection_string(self) -> str:

        sql = self.sqlserver

        parts = [
            f"DRIVER={{{sql['driver']}}}",
            f"SERVER={sql['server']}",
            f"DATABASE={sql['database']}",
            "TrustServerCertificate=yes",
        ]

        if sql.get("trusted_connection", False):

            parts.append("Trusted_Connection=yes")

        else:

            parts.append(f"UID={sql['user']}")
            parts.append(f"PWD={sql['password']}")

        return ";".join(parts) + ";"