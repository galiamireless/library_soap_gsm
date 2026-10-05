# Thinker: GUI Tk para microservicios

Thinker es la consola de escritorio Python/Tk para Login, Books/SOAP, Users, Authors, Orders y Payments. Presenta semáforos de salud, una sesión JWT y formularios CRUD. Electron no se modifica y puede seguir consumiendo el catálogo Books en el puerto 5001.

## Requisitos

- Windows 10/11.
- Python 3.11 o posterior, con Tkinter incluido.
- PostgreSQL instalado y accesible en `localhost:5432`.
- Redis en WSL es opcional: la caché del catálogo puede desactivarse si Redis no está disponible.

## Instalación desde cero

Abre CMD en la raíz `proyecto_bien`:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configura PostgreSQL desde una terminal que tenga `psql` en PATH. Cambia la contraseña de ejemplo por una propia:

```cmd
psql -U postgres -c "CREATE ROLE library_classifier_user LOGIN PASSWORD 'CAMBIA_ESTA_CLAVE';"
psql -U postgres -c "CREATE DATABASE library_classifier_db OWNER library_classifier_user;"
```

Ejecuta los esquemas y los datos de demostración en este orden:

```cmd
psql -U postgres -d library_classifier_db -f data\library_schema.sql
psql -U postgres -d library_classifier_db -f data\login_schema.sql
psql -U postgres -d library_classifier_db -f database\library_seed.sql
```

`login_schema.sql` incorpora `role_id` y actualiza las bases anteriores con la columna si aún no existe. Da permisos locales al usuario de aplicación:

```sql
GRANT USAGE ON SCHEMA library TO library_classifier_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA library TO library_classifier_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA library TO library_classifier_user;
```

Copia `.env.example` como `.env` si todavía no existe. Configura `DB_PASSWORD` con la contraseña del rol que acabas de crear. `JWT_SECRET_KEY` y `LOGIN_SECRET_KEY` deben ser iguales; para un entorno real usa una clave aleatoria, no el valor de ejemplo. Mantén `LOGIN_EMAIL_MODE=console` para desarrollo local: el enlace de verificación de Login aparecerá en la terminal que ejecuta Thinker.

## Iniciar Thinker

Desde la raíz `proyecto_bien`, con el entorno virtual activo:

```cmd
python thinker.py
```

Thinker inicia los servicios disponibles en `127.0.0.1` y abre la ventana Tk. No necesitas abrir seis terminales ni ejecutar los comandos individuales del README de microservicios. Al cerrar Thinker, se detienen los servidores que inició esta ventana.

Si ya hay un servicio ocupando uno de estos puertos, Thinker se conecta al servicio existente en vez de iniciar otro. Para que Users, Authors, Orders y Payments compartan su estado en memoria, cierra primero los servidores arrancados manualmente y después inicia Thinker. No ejecutes Thinker y `run_all_services.cmd` al mismo tiempo.

## Primera sesión y semáforos

1. En **Sesión de administración**, captura nombre, correo y una contraseña de al menos 8 caracteres.
2. Pulsa **Crear primer administrador**. El endpoint de bootstrap solo funciona desde `localhost` y una vez mientras la lista de Users está vacía.
3. Thinker inicia sesión automáticamente. Para sesiones posteriores, captura las mismas credenciales y usa **Iniciar sesión**.
4. El token se conserva solo en la memoria de la GUI; no se escribe a disco. Users emite JWT de 20 minutos. Cuando expire, vuelve a iniciar sesión. No hay endpoint de refresh.
5. Verde significa health correcto, rojo indica servicio o base de datos no disponible y ámbar indica Redis opcional sin responder. Login y SOAP necesitan PostgreSQL; Redis no es requisito para usar el catálogo.

El bootstrap crea un administrador del servicio Users, que es la autoridad de roles usada por los demás microservicios. Las cuentas del microservicio Login son otro recurso: se administran en **Login · Cuentas** y requieren JWT de administrador. Las cuentas nuevas de Login deben verificar su correo antes de iniciar sesión.

## Uso de los formularios CRUD

Cada pestaña tiene tabla y formulario. Pulsa **Actualizar lista** para leer, completa los campos y usa **Crear** para insertar. Selecciona una fila para cargarla en el formulario; usa **Guardar cambios** para editar o **Eliminar** para borrar. En Orders, `Artículos JSON` debe ser una lista, por ejemplo:

```json
[{"book_isbn":"9786070001001","quantity":1,"price":150}]
```

Payments requiere un pedido existente. Al registrar el pago, Payments notifica a Orders para cambiar el pedido a `paid`; al eliminar el pago de demostración, Orders vuelve a `pending`. La GUI envía JWT Bearer en las rutas protegidas. Sin sesión, los servicios devuelven 401; un rol insuficiente devuelve 403.

| Pestaña | Servicio / puerto | Operaciones disponibles |
|---|---:|---|
| Books · SOAP | 5001 | GET, POST, PUT, DELETE; lecturas XML/JSON y caché Redis opcional |
| Login · Cuentas | 5000 | GET, POST, PUT, DELETE de cuentas; verificación de correo en su subpestaña |
| Users · Perfiles | 5005 | GET, POST, PUT, DELETE; bootstrap inicial en localhost |
| Authors | 5006 | GET, POST, PUT, DELETE |
| Orders | 5007 | GET, POST, PUT/PATCH, DELETE |
| Payments | 5008 | GET, POST, PUT/PATCH, DELETE de demostración |

## Datos y persistencia

Books y las cuentas de Login se guardan en PostgreSQL. Users, Authors, Orders y Payments utilizan actualmente `STATE` en memoria de Python. Cuando Thinker inicia estos servicios en su propio proceso, comparten esa memoria durante la sesión; al cerrar Thinker esos datos de demostración se pierden. Para conservarlos entre reinicios se necesita migrar esos servicios a PostgreSQL u otro almacén compartido.

Redis solo cachea lecturas del catálogo SOAP (`GET /books` y `GET /books/<isbn>`) durante 180 segundos. La caché no es la fuente de verdad; si Redis está detenido, el catálogo consulta PostgreSQL. Para iniciarlo opcionalmente desde WSL:

```cmd
wsl -d Ubuntu -- sudo service redis-server start
wsl -d Ubuntu -- redis-cli ping
```

La respuesta `PONG` confirma que Redis está activo.

## Pruebas y verificación

En otra terminal, desde la misma carpeta y con `.venv` activo:

```cmd
python -m pytest apps\services\login\tests apps\services\soap\tests apps\services\test_microservices.py -q
```

Para verificar la salud manualmente, las direcciones son `http://127.0.0.1:5000/health`, `http://127.0.0.1:5001/health?format=json` y `/health` en los puertos 5005–5008. En la ventana de Thinker, los puntos de colores muestran el resultado.

## Electron

Electron permanece independiente y sin cambios. Con Thinker activo, abre otra terminal y ejecuta:

```cmd
cd apps\Electron-app
npm install
npm start
```

Configura el servicio como `http://127.0.0.1:5001` y el endpoint como `/books`. No inicies un segundo servidor SOAP en el mismo puerto.
