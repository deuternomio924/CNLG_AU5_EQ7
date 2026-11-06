# Evidencia E9 - Aplicacion al PIA (renta de vehiculos)

## Matriz CSV
Ver `datos/matriz_casos_pia.csv` (9 casos, 3 reglas, cada una con exito/error/limite).

## Pruebas ejecutables
`tests/test_renta_dominio.py`, `tests/test_renta_servicio.py`, `tests/test_renta_matriz_csv.py`.
Cada fila CP-01..CP-09 enlaza con su funcion en la columna `Prueba_pytest`.

## Reporte de cobertura del codigo pertinente
(Pegar aqui: captura de la terminal con PASSED + resumen `term-missing`, y captura de `htmlcov/index.html`.)

## Explicacion de las decisiones de diseno
1. Dominio puro separado de persistencia: las reglas (adeudo, stock, licencia, checklist, serie, tolerancia)
   se prueban sin base de datos; la BD solo interviene en las pruebas de integracion.
2. Una transaccion por caso de uso (`_transaccion`): commit si todo sale bien y rollback ante cualquier
   excepcion. CP-08 lo demuestra: la bitacora de recepcion se registra antes de validar la serie y el
   rollback la deshace, dejando contrato ACTIVO y vehiculo RENTADO.
3. Pasarela de pagos con `Mock(spec=["verificar_pago"])`: no hay cobro real; se verifica la llamada con el
   folio y que NO se invoca cuando la licencia o el checklist ya bloquean la entrega.
4. Limites explicitos: 29 min sin cargo y 30 min con cargo; ultima unidad de stock reservable; serie
   comparada de forma estricta (distingue mayusculas y espacios).
5. Supuesto a confirmar con el cliente: la regla solo dice que al minuto 30 se cobra una hora extra; se
   implemento "por hora iniciada" (61 min = 2 horas). Ajustar si el PIA define otra cosa.
