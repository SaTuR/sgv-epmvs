# Ciclo QA 1 — SGV EPMVS

Fecha: 2026-10-05  
Rama: develop

## Alcance

- Autenticación y sesión
- Clientes
- Predios
- Reservas
- Liberación de solar
- Compra confirmada
- Plan de cuotas
- Pagos
- Cartera
- Reportes
- Documentos PDF
- Roles y permisos
- Auditoría
- Regresión visual básica

## Severidad

- P1: impide operación o compromete integridad financiera/seguridad
- P2: función importante incorrecta con alternativa temporal
- P3: defecto menor o visual

## Casos automatizados

| ID | Caso | Resultado esperado |
|---|---|---|
| QA-A01 | Health + PostgreSQL | 200 y database=ok |
| QA-A02 | Login con contraseña incorrecta | 401 |
| QA-A03 | Usuario sin permiso intenta administrar usuarios | 403 |
| QA-A04 | Reservar dos veces el mismo solar | segundo intento 409 |
| QA-A05 | Liberar solar sin reservations.release | 403 |
| QA-A06 | Liberar solar con reservations.release | reserva inactiva + solar Disponible |
| QA-A07 | Compra 100% pagada con entrada | 0 cuotas; predio Pagado |
| QA-A08 | Pago mayor al saldo | 400 |
| QA-A09 | Reporte Recaudación incluye entrada | aparece movimiento ENTRADA |
| QA-A10 | PDF directo sin permiso | 403 |
| QA-A11 | Código público inexistente | 404 |

## Pruebas manuales

| ID | Módulo | Procedimiento | Resultado esperado | Estado |
|---|---|---|---|---|
| QA-M01 | Login | Credenciales válidas | Ingresa al Dashboard | PENDIENTE |
| QA-M02 | Login | Credenciales inválidas | Mensaje de error, no ingresa | PENDIENTE |
| QA-M03 | Clientes | Crear cliente válido | Cliente aparece en listado | PENDIENTE |
| QA-M04 | Clientes | Repetir identificación | Operación rechazada | PENDIENTE |
| QA-M05 | Predios | Crear predio Disponible | Aparece con color definido | PENDIENTE |
| QA-M06 | Reservas | Reservar solar Disponible | Estado pasa a Reservado | PENDIENTE |
| QA-M07 | Reservas | Intentar reservar solar Reservado | No permitido | PENDIENTE |
| QA-M08 | Reserva | Usuario sin permiso liberar | Botón oculto y API denegada | PENDIENTE |
| QA-M09 | Reserva | Usuario autorizado libera | Solar vuelve a Disponible | PENDIENTE |
| QA-M10 | Auditoría | Revisar liberación | Usuario/IP/acción registrados | PENDIENTE |
| QA-M11 | Ventas | Confirmar compra desde reserva | Predio En proceso de pago | PENDIENTE |
| QA-M12 | Cuotas | Financiar 9.000 en 9 cuotas | suma de cuotas = 9.000 exactos | PENDIENTE |
| QA-M13 | Ventas | Entrada = precio total | Sin cuotas; predio Pagado | PENDIENTE |
| QA-M14 | Pagos | Pago parcial | Se aplica a cuota más antigua | PENDIENTE |
| QA-M15 | Pagos | Pago supera saldo | Operación rechazada | PENDIENTE |
| QA-M16 | Pagos | Pagar saldo completo | Predio pasa a Pagado | PENDIENTE |
| QA-M17 | Cartera | Compra con saldo | Aparece saldo correcto | PENDIENTE |
| QA-M18 | Cartera | Cuota vencida | Monto y días de mora correctos | PENDIENTE |
| QA-M19 | Dashboard | Comparar total recaudado | Entrada + pagos coincide | PENDIENTE |
| QA-M20 | Reporte Recaudación | Comparar contra Dashboard | Totales conciliados | PENDIENTE |
| QA-M21 | Reporte Predios | Filtro por etapa/estado | Solo registros esperados | PENDIENTE |
| QA-M22 | CSV | Exportar cada reporte | Archivo abre y contiene datos filtrados | PENDIENTE |
| QA-M23 | PDF | Comprobante de pago | Logo, datos, valores, QR, número | PENDIENTE |
| QA-M24 | PDF | Estado de cuenta | Cuotas/saldo correctos | PENDIENTE |
| QA-M25 | PDF | Certificado pagos | Entrada + pagos y saldo correctos | PENDIENTE |
| QA-M26 | Certificados | Reimprimir documento | Conserva número original | PENDIENTE |
| QA-M27 | QR | Consultar código válido | Documento válido | PENDIENTE |
| QA-M28 | Roles | Quitar documents.view | Certificados desaparece del menú | PENDIENTE |
| QA-M29 | Roles | Acceder URL/API sin permiso | 403 | PENDIENTE |
| QA-M30 | UI | Revisar estados en pantallas | Misma paleta en todas | PENDIENTE |

## Defectos encontrados en revisión QA

### QA-D01 — P1 — Recaudación omitía entradas
Dashboard sumaba entrada inicial + pagos, pero Reporte Recaudación mostraba solo pagos posteriores.

Corrección: el reporte incluye ahora un movimiento sintético de tipo ENTRADA en la fecha de confirmación de compra.

### QA-D02 — P1 — PDFs directos no exigían permiso funcional
Algunos endpoints PDF aceptaban cualquier usuario autenticado.

Corrección: comprobantes requieren payments.manage o documents.view; estados/certificados requieren sales.manage o documents.view.

### QA-D03 — P1 — Compra pagada 100% generaba cuotas de valor cero
Si down_payment == sale_price, se creaba plan con cuotas $0.

Corrección: compra totalmente pagada registra 0 cuotas y predio Pagado.

## Criterio de salida del Ciclo QA 1

- 0 defectos P1 abiertos
- 0 defectos P2 bloqueantes
- Todos los casos automatizados en verde
- QA-M01 a QA-M30 ejecutados o justificados como no aplicables
