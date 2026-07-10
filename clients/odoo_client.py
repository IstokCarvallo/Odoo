import xmlrpc.client


class OdooClient:
    """
    Cliente genérico para consumir la API XML-RPC de Odoo.
    No contiene lógica de negocio.
    """

    def __init__(self, settings: dict):
        self._settings = settings
        self._uid = None
        self._models = None

    @property
    def uid(self):
        return self._uid

    def connect(self):
        """
        Autentica el usuario y crea el proxy de objetos.
        """

        common = xmlrpc.client.ServerProxy(f"{self._settings['url']}/xmlrpc/2/common")

        self._uid = common.authenticate(
            self._settings["database"],
            self._settings["username"],
            self._settings["api_key"],
            {}
        )

        if not self._uid:
            raise Exception("No fue posible autenticarse en Odoo.")

        self._models = xmlrpc.client.ServerProxy(f"{self._settings['url']}/xmlrpc/2/object")

    def execute(
        self,
        model: str,
        method: str,
        args=None,
        kwargs=None
    ):
        """
        Ejecuta cualquier método XML-RPC de Odoo.
        """

        if self._models is None:
            raise Exception("Debe ejecutar connect() antes de utilizar el cliente.")

        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        return self._models.execute_kw(
            self._settings["database"],
            self._uid,
            self._settings["api_key"],
            model,
            method,
            args,
            kwargs
        )