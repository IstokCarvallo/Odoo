from clients.odoo_client import OdooClient


MODELS = [
    "hr.contract",
    "hr.employee",
    "hr.department",
    "res.company",
    "resource.calendar"
]


def discover_models(client: OdooClient):
    for model in MODELS:

        print()
        print("=" * 100)
        print(f"MODELO : {model}")
        print("=" * 100)

        fields = client.execute(
            model=model,
            method="fields_get",
            kwargs={
                "attributes": [
                    "string",
                    "type",
                    "required"
                ]
            }
        )

        print(f"{'Campo':35} {'Tipo':15} {'Req.':6} Descripción")
        print("-" * 100)

        for field_name in sorted(fields.keys()):
            field = fields[field_name]
            required = "Sí" if field.get("required") else "No"
            custom = ""
            
            if field_name.startswith(("x_", "x_studio_")):
                custom = "★"

            print(
                f"{custom}{field_name:34}"
                f"{field.get('type',''):15}"
                f"{required:6}"
                f"{field.get('string','')}"
            )