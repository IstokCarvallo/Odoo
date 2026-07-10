# Análisis Modelo Odoo - ETL Personal

**Proyecto:** OdooPersonal
**Versión:** 1.0
**Fecha:** Julio 2026

---

# 1. Objetivo

Este documento define el modelo de datos que será utilizado por el proceso ETL encargado de extraer información de Odoo y cargarla en SQL Server para su posterior normalización e integración con el ERP corporativo.

El propósito del ETL es exclusivamente la extracción y persistencia de la información. Todas las reglas de negocio, homologaciones y procesos de carga al ERP serán responsabilidad de SQL Server mediante procedimientos almacenados.

---

# 2. Arquitectura del proceso

```
Odoo
   │
   ▼
ETL Python
   │
   ▼
STG_OdooContrato
   │
   ▼
SP_NormalizarPersonal
   │
   ▼
SP_CargarPersonalERP
   │
   ▼
ERP
```

---

# 3. Principios de diseño

## 3.1 El contrato es la entidad principal

El proceso se construye sobre el modelo **hr.contract**.

No se construye sobre el empleado.

Esto permite representar correctamente situaciones como:

* múltiples contratos
* cambio de empresa
* recontrataciones
* contratos históricos

Cada registro del ETL representa un contrato.

---

## 3.2 El ETL no contiene reglas de negocio

El código Python únicamente debe:

* conectarse a Odoo
* extraer información
* aplanar los datos
* cargar la tabla STG

No debe:

* homologar datos
* validar información
* construir lógica del ERP
* eliminar registros
* detectar cambios de negocio

---

## 3.3 SQL Server implementa las reglas

Toda la lógica funcional será implementada mediante procedimientos almacenados.

Ejemplos:

* homologación de empresas
* homologación de departamentos
* asignación de centros de costo
* carga al ERP
* detección de cambios

---

# 4. Modelo principal

Modelo Odoo:

```
hr.contract
```

Desde este modelo se obtienen las relaciones hacia:

* hr.employee
* hr.department
* res.company
* resource.calendar

---

# 5. Modelos relacionados

## hr.employee

Información personal del trabajador.

Campos relevantes identificados:

* id
* firstname
* middle_name
* last_name
* mothers_name
* identification_id
* department_id
* company_id

---

## hr.department

Información del departamento.

Campos relevantes:

* id
* name

---

## res.company

Información de la empresa.

Campos relevantes:

* id
* name
* parent_id

---

## resource.calendar

Información del calendario laboral.

Campos relevantes:

* id
* name

---

# 6. Campos identificados

## Confirmados

| Modelo      | Campo                |
| ----------- | -------------------- |
| hr.contract | id                   |
| hr.contract | name                 |
| hr.contract | state                |
| hr.contract | employee_id          |
| hr.contract | company_id           |
| hr.contract | department_id        |
| hr.contract | resource_calendar_id |
| hr.contract | date_start           |
| hr.contract | date_end             |

---

## hr.employee

| Campo             |
| ----------------- |
| id                |
| firstname         |
| middle_name       |
| last_name         |
| mothers_name      |
| identification_id |

---

# 7. Campos personalizados encontrados

Durante el análisis se identificaron campos personalizados en la instancia Odoo.

Ejemplos:

* x_studio_empresa_principal
* x_studio_rut
* x_ex_state

Estos campos deberán evaluarse antes de la implementación definitiva del extractor.

---

# 8. Campos pendientes de análisis

## Centro de costo

No fue identificado un campo estándar que represente el centro de costo.

Se deberá determinar si:

* corresponde a un campo personalizado
* proviene de otro modelo
* se obtiene mediante una relación adicional

Hasta confirmar esta información no se incorporará al ETL.

---

## Cargo

Debe analizarse si corresponde extraer:

```
job_id
```

desde el contrato o desde el empleado.

---

# 9. Diseño de la tabla STG

La tabla de staging utilizará el nombre:

```
STG_OdooContrato
```

Cada fila representa un contrato existente en Odoo.

No representa un empleado.

---

## Columnas preliminares

* ContratoId
* NombreContrato
* EstadoContrato
* EmpleadoId
* Rut
* PrimerNombre
* SegundoNombre
* ApellidoPaterno
* ApellidoMaterno
* DepartamentoId
* Departamento
* EmpresaId
* Empresa
* EmpresaPadreId
* EmpresaPadre
* CalendarioId
* Calendario
* FechaInicioContrato
* FechaFinContrato
* CentroCostoId (pendiente)
* CentroCosto (pendiente)
* FechaExtraccion
* ExecutionId
* Procesado
* FechaProceso
* RegistroHash

---

# 10. Campos descartados

## NombreCompleto

No será persistido.

Es un dato derivable.

Puede construirse cuando sea necesario desde los nombres y apellidos.

---

# 11. Próximas actividades

1. Confirmar origen del centro de costo.
2. Confirmar origen del RUT definitivo.
3. Diseñar STG_OdooContrato.sql.
4. Implementar PersonalExtractor.
5. Implementar SqlRepository.
6. Construir el flujo ETL completo.
