# Metricas SOAP y reflexion

Registrar durante la ejecucion final:

| Metrica | Resultado |
|---|---|
| Tiempo de desarrollo | Completar con horas reales |
| LOC de `app.py`, `config/`, `db/`, `soap/` | Ejecutar `Get-ChildItem -Recurse *.py \| Get-Content \| Measure-Object -Line` |
| LOC del cliente | Medir `clients/` por separado |
| Bytes request RegistrarClasificacion | Medir `len(xml.encode('utf-8'))` |
| Bytes response | Medir cuerpo HTTP |
| Porcentaje estructura XML | `(bytes totales - bytes de valores)/bytes totales * 100` |

Preguntas: un campo obligatorio nuevo rompe clientes document/literal si no se versiona; el WSDL revela operaciones y tipos pero no debe contener secretos; XSD aporta enumeraciones y obligatoriedad; Envelope y namespaces son boilerplate, Body depende de la operacion. SOAP se justifica cuando hay contratos formales, Fault tipado, WS-* o clientes empresariales heterogeneos. La GUI muestra mensajes funcionales para Fault Client y un mensaje neutro para Fault Server. Compartir BD crea acoplamiento y riesgo de permisos, mitigado por vistas, repositorio y rol dedicado. WS-Security autentica el mensaje/operacion; no basta confiar en el correo recibido.
