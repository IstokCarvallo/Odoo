from clients.odoo_client import OdooClient


class DiscoverModel:
    """
    Herramienta para inspeccionar cualquier modelo de Odoo.

    Permite:
    - Mostrar la definición de todos los campos.
    - Mostrar registros de ejemplo.
    """

    def __init__(self, client: OdooClient):
        self._client = client

    def inspect(
        self,
        model: str,
        limit: int = 3,
    ) -> None:

        print()
        print("=" * 120)
        print(f"MODELO: {model}")
        print("=" * 120)

        # ---------------------------------------------------------
        # Definición de campos
        # ---------------------------------------------------------

        fields = self._client.execute(
            model=model,
            method="fields_get",
            kwargs={
                "attributes": [
                    "string",
                    "type",
                    "required",
                ]
            },
        )

        print()
        print("CAMPOS")
        print("-" * 120)
        print(f"{'Campo':35} {'Tipo':15} {'Req.':6} Descripción")
        print("-" * 120)

        for field_name in sorted(fields):

            field = fields[field_name]

            custom = ""

            if field_name.startswith(("x_", "x_studio_")):
                custom = "★"

            required = "Sí" if field.get("required") else "No"

            print(
                f"{custom}{field_name:34}"
                f"{field.get('type',''):15}"
                f"{required:6}"
                f"{field.get('string','')}"
            )

        # ---------------------------------------------------------
        # Registros de ejemplo
        # ---------------------------------------------------------

        print()
        print("=" * 120)
        print("REGISTROS")
        print("=" * 120)

        records = self._client.execute(
            model=model,
            method="search_read",
            args=[[]],
            kwargs={
                "limit": limit,
            },
        )

        for index, record in enumerate(records, start=1):

            print()
            print("-" * 120)
            print(f"Registro {index}")
            print("-" * 120)

            for key in sorted(record.keys()):

                print(f"{key:35}: {record[key]}")