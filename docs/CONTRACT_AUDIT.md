# Auditoria del contrato WSDL

| Dato | Operacion | Exposicion | Justificacion |
|---|---|---|---|
| ISBN | Pendientes/Registrar | Si | Identifica el libro sin exponer precio o stock |
| Titulo | Pendientes | Si | Permite reconocer el libro |
| Nombre de concepto | Pendientes | Si | Es la unidad de trabajo |
| Definicion | Pendientes | Si | Da contexto para clasificar |
| Categoria | Pendientes | Si, transformada desde genres | El contrato usa una palabra estable aunque E2 tenga generos |
| Modelo Cloud | Registrar/Estadisticas | Si | Capacidad principal del modulo |
| Correo del clasificador | Registrar/Progreso | Si, entrada | Identifica progreso; no es autenticacion |
| Nombre y apellidos | Registrar | Si, entrada | Auditoria funcional minima |
| Conteos | Progreso/Estadisticas | Si | Resultado necesario para cliente |
| Precio, stock, password_hash, sesiones | Ninguna | No | Minimo privilegio y privacidad |
| IDs internos de tablas de auditoria | Ninguna | No | Evita acoplar clientes a persistencia |

El contrato es estricto: los tipos Cloud son una enumeracion XSD y los elementos obligatorios no se omiten. Agregar un elemento obligatorio rompe clientes antiguos; por eso una evolucion compatible debe agregar elementos opcionales o versionar el namespace.
