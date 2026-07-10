import json
from pathlib import Path


class Settings:
    """
    Carga la configuración del proyecto desde config.json.
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

    @property
    def odoo(self):
        return self._config["odoo"]

    @property
    def sqlserver(self):
        return self._config["sqlserver"]