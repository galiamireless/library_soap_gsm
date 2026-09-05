# Library Classifier SOAP

Modulo independiente Flask + psycopg para clasificar conceptos del catalogo de E2. El monolito Node.js no se modifica. El servicio comparte PostgreSQL unicamente para este ejercicio y escribe solo en sus tablas propias.

## Alcance

Incluye `ObtenerConceptosPendientes`, `RegistrarClasificacion`, `ObtenerProgresoUsuario` y `ObtenerEstadisticasPorModelo`. Los modelos validos son `IaaS`, `PaaS`, `SaaS` y `FaaS`. La estadistica exige `UsernameToken` WS-Security. No incluye REST, migracion del monolito, acceso de clientes a PostgreSQL ni Spyne/Zeep para generar sobres.

El esquema de E2 no tiene `categories`; la relacion real es `books -> book_genres -> genres`. Por eso el contrato expone el campo estable `category`, derivado de `genres`, sin cambiar ninguna tabla existente.

## Instalacion local

```powershell
cd E3/Apps/library_soap_service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Ejecutar `sql/soap_module.sql` con el usuario administrador de PostgreSQL. Crear un rol de aplicacion separado y aplicar los `GRANT` comentados al final del script. Nunca usar `postgres` desde Flask.

Completar `.env` con la conexion de E2. Para crear un hash local sin guardar la contraseña:

```powershell
python -c "from soap.security import password_hash; print(password_hash('cambia-esta-clave'))"
```

Pegar el hash en `SOAP_USER_HASHES=classifier:<hash>`. No versionar `.env`.

## Ejecucion

```powershell
$env:PYTHONPATH='.'
python app.py
```

- WSDL: `http://127.0.0.1:5000/library-classifier.wsdl`
- SOAP endpoint: `http://127.0.0.1:5000/soap`
- Health: `http://127.0.0.1:5000/health`

## Pruebas

```powershell
$env:PYTHONPATH='.'
python -m pytest -q
```

Las pruebas unitarias cubren lista de pendientes, modelo invalido, XML invalido y autenticacion. Las pruebas de integracion deben ejecutarse con PostgreSQL disponible, el SQL aplicado y conceptos reales de E2.

## Interoperabilidad

`clients/desktop_client.py` construye el Envelope con la libreria estandar y nunca abre una conexion SQL. `clients/classifier_gui.py` ofrece una GUI Tkinter que captura nombre, apellidos, correo, ISBN, concepto y modelo. Para generar un cliente Java desde el contrato:

```powershell
wsimport -keep -p generated http://127.0.0.1:5000/library-classifier.wsdl
javac clients/java/LibrarySoapClient.java
java -cp clients/java LibrarySoapClient
```

El archivo Java incluido muestra el consumo desde otro lenguaje; la comparacion manual/generado queda documentada en `docs/ARCHITECTURE.md`.

## Errores SOAP

- XML invalido o campos faltantes: `soap:Client`, HTTP 400.
- Concepto inexistente: `soap:Client`, HTTP 400.
- Modelo no permitido: `soap:Client`, HTTP 400.
- Clasificacion duplicada: `soap:Client`, HTTP 409 y detalle `CONFLICT_409`.
- Credenciales incorrectas: `soap:Client`, HTTP 401.
- Error de PostgreSQL: `soap:Server`, HTTP 500; el detalle tecnico queda solo en el log.

## Estructura

`app.py` publica Flask; `config/` carga ambiente; `db/` concentra SQL parametrizado y transacciones; `soap/` procesa XML, faults y seguridad; `wsdl/` contiene contrato; `sql/` contiene tablas propias; `clients/` contiene GUI, cliente manual y cliente Java; `tests/` contiene pruebas; `docs/` y `report/` contienen evidencia y reporte.
