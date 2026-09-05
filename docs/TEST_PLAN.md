# Parte 9. Plan de pruebas y evidencias

| ID | Entrada | Resultado esperado | Resultado obtenido | Evidencia | Conclusion |
|---|---|---|---|---|---|
| P01 | Obtener pendientes con cliente valido | Lista real de conceptos, libro y categoria | `pytest` simulado; repetir con BD | `images/T3/2.PNG` | El contrato devuelve datos mínimos |
| P02 | Registrar IaaS, PaaS, SaaS y FaaS | Cuatro registros válidos | Repetir con conceptos reales de varios libros | `images/T3/3.PNG` | Los cuatro modelos se validan |
| P03 | Obtener progreso de usuario | Totales clasificados y pendientes | Repetir con correo registrado | `images/T3/4.PNG` | El progreso se calcula por clasificador |
| P04 | Estadísticas con UsernameToken válido | Conteo por modelo | Repetir con hash local | `images/T3/5.PNG` | La operación sensible exige autenticación |
| N01 | Repetir mismo clasificador/concepto | SOAP Fault HTTP 409 | Restricción UNIQUE y Fault `CONFLICT_409` | `images/T3/6.PNG` | El duplicado no se registra |
| N02 | `concept_id` inexistente | SOAP Fault Client HTTP 400 | Repositorio valida la relación | `images/T3/7.PNG` | Se rechaza antes de insertar |
| N03 | Modelo `Invalid` | SOAP Fault de validación HTTP 400 | Prueba automatizada aprobada | `images/T3/8.PNG` | Solo se aceptan cuatro modelos |
| N04 | XML truncado | SOAP Fault Client HTTP 400 | Prueba automatizada aprobada | `images/T3/9.PNG` | No se ejecuta SQL |
| N05 | Credencial WS-Security incorrecta | SOAP Fault HTTP 401 | Prueba automatizada aprobada | `images/T3/10.PNG` | No se revela el secreto |
| N06 | PostgreSQL apagado | SOAP Fault Server HTTP 500 y log técnico | Ejecutar con BD inaccesible | `images/T3/11.PNG` | Se separa mensaje público de detalle interno |

## Resultado automatizado disponible

```text
python -m pytest -q
4 passed
```

## Verificacion PostgreSQL

```sql
SELECT concept_id, isbn, modelo_cloud, classified_at FROM clasificaciones_cloud ORDER BY classified_at;
SELECT tipo_cliente, identificador, peticiones_atendidas FROM clientes_servidos ORDER BY ultima_peticion;
SELECT c.correo, COUNT(*) FROM clasificadores c JOIN clasificaciones_cloud cc USING (clasificador_id) GROUP BY c.correo;
```

Conservar para la entrega el WSDL, request/response exitoso, Envelope de cada Fault, captura de GUI, salida de pytest y estas consultas. No incluir `.env`, hashes reutilizables, contraseñas ni cadenas de conexion.

## Orden de evidencias

La primera captura del ejercicio guiado es `../images/T3/1.PNG`; las siguientes continúan consecutivamente. La sección 1 usa `1.PNG`, la arquitectura y decisiones usan capturas posteriores, y esta matriz termina en `11.PNG`. Las tareas en casa comienzan después con la misma secuencia.
