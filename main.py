import xmlrpc.client 
from pprint import pprint

from config.settings import Settings
from clients.odoo_client import OdooClient
from tools.discover_models import discover_models


# # Credenciales con API Key
url = "https://rioblanco-prueba-34692340.dev.odoo.com/"  # SIN /odoo al final
db = "rioblanco-prueba-34692340"
username = "admin"  # El mismo usuario
api_key = "b122691c59cd77a7ed3eb6379a3d8285539804b7"  # API Key del usuario

# Conectar a Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, api_key, {})

if not uid:
    print("Error de autenticación")
    exit()

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def get_contracts_with_all_details(limit=10):
    """
    Obtiene contratos con todos los detalles requeridos:
    - Datos del empleado (RUT, nombres por separado, sucursal del empleado)
    - Datos de la compañía (sucursal principal)
    - Datos del departamento
    - Datos del calendario
    """
 
    # 1. Obtener contratos con campos básicos
    contracts = models.execute_kw(
        db, uid, api_key,
        'hr.contract', 'search_read',
        [[('state', 'in', ['open', 'close'])]],
        {
            'fields': [
                'id', 'name', 'state',  # Contrato
                'employee_id',  # Empleado
                'department_id',  # Departamento del contrato
                'company_id',  # Compañía/Sucursal del contrato
                'resource_calendar_id'  # Calendario
            ],
            'limit': limit,
            'order': 'id desc'
        }
    )
 
    if not contracts:
        print("No se encontraron contratos")
        return []
 
    # 2. Extraer todos los IDs relacionados
    employee_ids = []
    department_ids = []
    company_ids = []
    calendar_ids = []
    parent_company_ids = []
 
    for contract in contracts:
        if contract.get('employee_id'):
            emp_id = contract['employee_id'][0]
            if emp_id not in employee_ids:
                employee_ids.append(emp_id)
     
        if contract.get('department_id'):
            dept_id = contract['department_id'][0]
            if dept_id not in department_ids:
                department_ids.append(dept_id)
     
        if contract.get('company_id'):
            comp_id = contract['company_id'][0]
            if comp_id not in company_ids:
                company_ids.append(comp_id)
     
        if contract.get('resource_calendar_id'):
            cal_id = contract['resource_calendar_id'][0]
            if cal_id not in calendar_ids:
                calendar_ids.append(cal_id)
 
    # 3. Obtener datos de empleados (RUT y nombres separados)
    employees = {}
    if employee_ids:
        emp_data = models.execute_kw(
            db, uid, api_key,
            'hr.employee', 'search_read',
            [[('id', 'in', employee_ids)]],
            {
                'fields': [
                    'id',
                    'identification_id',  # ← RUT del empleado
                    'firstname',          # ← Primer nombre
                    'middle_name',        # ← Segundo nombre
                    'last_name',          # ← Apellido paterno
                    'mothers_name',       # ← Apellido materno
                    'name',               # ← Nombre completo (opcional)
                    'company_id',         # ← Sucursal del empleado
                    'department_id'       # ← Departamento del empleado
                ]
            }
        )
        employees = {e['id']: e for e in emp_data}
     
        # Extraer company_ids de empleados
        for emp in emp_data:
            if emp.get('company_id'):
                comp_id = emp['company_id'][0]
                if comp_id not in company_ids:
                    company_ids.append(comp_id)
          
            # Extraer department_ids de empleados
            if emp.get('department_id'):
                dept_id = emp['department_id'][0]
                if dept_id not in department_ids:
                    department_ids.append(dept_id)
 
    # 4. Obtener datos de departamentos
    departments = {}
    if department_ids:
        dept_data = models.execute_kw(
            db, uid, api_key,
            'hr.department', 'search_read',
            [[('id', 'in', department_ids)]],
            {'fields': ['id', 'name', 'company_id']}
        )
        departments = {d['id']: d for d in dept_data}
     
        # Extraer company_ids de departamentos
        for dept in dept_data:
            if dept.get('company_id'):
                comp_id = dept['company_id'][0]
                if comp_id not in company_ids:
                    company_ids.append(comp_id)
 
    # 5. Obtener datos de compañías/sucursales
    companies = {}
    parent_company_ids = []
 
    if company_ids:
        # Obtener compañías principales
        comp_data = models.execute_kw(
            db, uid, api_key,
            'res.company', 'search_read',
            [[('id', 'in', company_ids)]],
            {'fields': ['id', 'name', 'parent_id']}
        )
        companies = {c['id']: c for c in comp_data}
     
        # Extraer parent_ids
        for comp in comp_data:
            if comp.get('parent_id'):
                parent_id = comp['parent_id'][0]
                if parent_id not in parent_company_ids and parent_id not in company_ids:
                    parent_company_ids.append(parent_id)
     
        # Obtener compañías padre si existen
        if parent_company_ids:
            parent_data = models.execute_kw(
                db, uid, api_key,
                'res.company', 'search_read',
                [[('id', 'in', parent_company_ids)]],
                {'fields': ['id', 'name']}
            )
            for p in parent_data:
                companies[p['id']] = p
 
    # 6. Obtener datos de calendarios
    calendars = {}
    if calendar_ids:
        cal_data = models.execute_kw(
            db, uid, api_key,
            'resource.calendar', 'search_read',
            [[('id', 'in', calendar_ids)]],
            {'fields': ['id', 'name']}
        )
        calendars = {c['id']: c for c in cal_data}
 
    # 7. Combinar todos los datos
    result = []
    for contract in contracts:
        # Datos del empleado (con RUT y nombres separados)
        emp_id = contract['employee_id'][0] if contract.get('employee_id') else None
        emp_data = employees.get(emp_id, {})
       
        # CONSTRUIR NOMBRE COMPLETO (opcional)
        nombre_completo = f"{emp_data.get('firstname', '')} {emp_data.get('middle_name', '')} {emp_data.get('last_name', '')} {emp_data.get('mothers_name', '')}".strip()
      
        # Sucursal del empleado (employee.company_id)
        emp_company_id = emp_data.get('company_id', [None])[0] if emp_data.get('company_id') else None
        emp_company_data = companies.get(emp_company_id, {})
      
        # Departamento del empleado
        emp_department_id = emp_data.get('department_id', [None])[0] if emp_data.get('department_id') else None
        emp_department_data = departments.get(emp_department_id, {})
     
        # Datos del departamento del contrato
        dept_id = contract['department_id'][0] if contract.get('department_id') else None
        dept_data = departments.get(dept_id, {})
      
        # Datos de la compañía/sucursal del contrato
        comp_id = contract['company_id'][0] if contract.get('company_id') else None
        comp_data = companies.get(comp_id, {})
     
        # Compañía padre (si existe)
        parent_id = comp_data.get('parent_id', [False])[0] if comp_data.get('parent_id') else None
        parent_data = companies.get(parent_id, {})
     
        # Datos del calendario
        cal_id = contract['resource_calendar_id'][0] if contract.get('resource_calendar_id') else None
        cal_data = calendars.get(cal_id, {})
     
        # Construir registro completo con campos EXPLÍCITAMENTE SEPARADOS
        record = {
            'id': contract['id'],
            'nombre_contrato': contract['name'],
            'estado': contract['state'],
         
            # ==========================================================
            # DATOS DEL EMPLEADO CON CAMPOS SEPARADOS
            # ==========================================================
            'empleado': {
                'id': emp_id,
                'rut': emp_data.get('identification_id'),      # ← RUT separado
                'primer_nombre': emp_data.get('firstname'),    # ← Primer nombre
                'segundo_nombre': emp_data.get('middle_name'), # ← Segundo nombre
                'apellido_paterno': emp_data.get('last_name'), # ← Apellido paterno
                'apellido_materno': emp_data.get('mothers_name'), # ← Apellido materno
                'nombre_completo': nombre_completo,            # ← Combinado (opcional)
               
                # SUCURSAL DEL EMPLEADO (company_id)
                'sucursal': {
                    'id': emp_company_id,
                    'nombre': emp_company_data.get('name')
                } if emp_company_data else None,
               
                # Departamento del empleado
                'departamento': {
                    'id': emp_department_id,
                    'nombre': emp_department_data.get('name')
                } if emp_department_data else None,
            } if emp_data else None,
         
            # ==========================================================
            # DATOS DEL DEPARTAMENTO DEL CONTRATO
            # ==========================================================
            'departamento_contrato': {
                'id': dept_id,
                'nombre': dept_data.get('name')
            } if dept_data else None,
         
            # ==========================================================
            # DATOS DE LA COMPAÑÍA/SUCURSAL DEL CONTRATO
            # ==========================================================
            'sucursal_contrato': {
                'id': comp_id,
                'nombre': comp_data.get('name'),
                'sucursal_padre': {
                    'id': parent_id,
                    'nombre': parent_data.get('name')
                } if parent_data else None
            } if comp_data else None,
         
            # ==========================================================
            # DATOS DEL CALENDARIO
            # ==========================================================
            'calendario': {
                'id': cal_id,
                'nombre': cal_data.get('name')
            } if cal_data else None
        }
     
        result.append(record)
 
    return result

# Función para imprimir los resultados mostrando CAMPOS SEPARADOS
def print_contracts(contracts):
    for reg in contracts:
        print("\n" + "=" * 60)
        print(f"CONTRATO: {reg.get('nombre_contrato', 'N/A')} (ID: {reg.get('id')})")
        print("=" * 60)
      
        # ==========================================================
        # IMPRIMIR DATOS DEL EMPLEADO CON CAMPOS SEPARADOS
        # ==========================================================
        if reg['empleado']:
            emp = reg['empleado']
            print(f"EMPLEADO:")
            print(f"  ID: {emp.get('id')}")
            print(f"  ★ RUT: {emp.get('rut', 'N/A')}")  # ← RUT separado
            print(f"  ★ Primer nombre: {emp.get('primer_nombre', 'N/A')}")  # ← Campo separado
            print(f"  ★ Segundo nombre: {emp.get('segundo_nombre', 'N/A')}")  # ← Campo separado
            print(f"  ★ Apellido paterno: {emp.get('apellido_paterno', 'N/A')}")  # ← Campo separado
            print(f"  ★ Apellido materno: {emp.get('apellido_materno', 'N/A')}")  # ← Campo separado
            print(f"  Nombre completo: {emp.get('nombre_completo', 'N/A')}")  # Opcional
           
            # Sucursal del empleado (COMPANY_ID)
            if emp.get('sucursal'):
                print(f"  ★ Sucursal del empleado: {emp['sucursal'].get('nombre', 'N/A')}")
            else:
                print(f"  ★ Sucursal del empleado: N/A")
           
            # Departamento del empleado
            if emp.get('departamento'):
                print(f"  Departamento del empleado: {emp['departamento'].get('nombre', 'N/A')}")
        else:
            print("EMPLEADO: N/A")
      
        # Estado del contrato
        print(f"\nESTADO DEL CONTRATO: {reg.get('estado', 'N/A')}")
      
        # Departamento del contrato
        if reg.get('departamento_contrato'):
            print(f"\nDEPARTAMENTO DEL CONTRATO: {reg['departamento_contrato'].get('nombre', 'N/A')}")
      
        # Compañía/Sucursal del contrato
        if reg.get('sucursal_contrato'):
            comp = reg['sucursal_contrato']
            print(f"\n★ COMPAÑÍA/SUCURSAL DEL CONTRATO: {comp.get('nombre', 'N/A')}")
            if comp.get('sucursal_padre'):
                print(f"  Compañía padre: {comp['sucursal_padre'].get('nombre', 'N/A')}")
      
        # Calendario
        if reg.get('calendario'):
            cal = reg['calendario']
            print(f"\nCALENDARIO: {cal.get('nombre', 'N/A')}")
      
        print("-" * 60)

# Función simplificada para mostrar SOLO los campos requeridos
def print_contracts_simple(contracts):
    print("\n" + "=" * 80)
    print("RESUMEN DE CONTRATOS - CAMPOS REQUERIDOS")
    print("=" * 80)
   
    for idx, reg in enumerate(contracts, 1):
        print(f"\n【 Contrato {idx} 】")
       
        if reg['empleado']:
            emp = reg['empleado']
            print(f"  ✓ RUT del empleado: {emp.get('rut', 'No especificado')}")
            print(f"  ✓ Primer nombre: {emp.get('primer_nombre', 'No especificado')}")
            print(f"  ✓ Segundo nombre: {emp.get('segundo_nombre', 'No especificado')}")
            print(f"  ✓ Apellido paterno: {emp.get('apellido_paterno', 'No especificado')}")
            print(f"  ✓ Apellido materno: {emp.get('apellido_materno', 'No especificado')}")
           
            # ★ SUCURSAL DEL EMPLEADO (campo requerido)
            if emp.get('sucursal'):
                print(f"  ✓ Sucursal del empleado: {emp['sucursal'].get('nombre', 'No especificado')}")
            else:
                print(f"  ✗ Sucursal del empleado: No asignada")
       
        # ★ COMPAÑÍA/SUCURSAL DEL CONTRATO
        if reg.get('sucursal_contrato'):
            print(f"  ✓ Compañía del contrato: {reg['sucursal_contrato'].get('nombre', 'No especificado')}")
        else:
            print(f"  ✗ Compañía del contrato: No asignada")
           
        print(f"  Estado: {reg.get('estado', 'N/A')}")
        print("-" * 40)


def main():
    print("=" * 60)
    print("ODDO PERSONAL")
    print("=" * 60)

    settings = Settings()

    print()
    print("Conectando a Odoo...")

    client = OdooClient(settings.odoo)
    client.connect()

    print("Autenticación exitosa.")
    discover_models(client)

# Ejecutar
if __name__ == "__main__":

    main()
    # print("=" * 60)
    # print("OBTENIENDO CONTRATOS CON CAMPOS SEPARADOS")
    # print("(RUT y nombres del empleado están en campos distintos)")
    # print("=" * 60)
 
    # # Obtener contratos
    # contracts = get_contracts_with_all_details(limit=10)
   
    # if contracts:
    #     # Mostrar versión simple con los campos requeridos
    #     # print_contracts_simple(contracts)
       
    #     # Opcional: Mostrar versión detallada
    #     print_contracts(contracts)
    # else:
    #     print("No se encontraron contratos")
