# Evidencias del login

Estas instrucciones generan las evidencias desde CMD sin modificar `Electron-app` ni el servicio del catalogo. No es necesario usar `psql`: `psql` es solamente una herramienta de consola para administrar PostgreSQL. El entorno virtual se activa desde CMD con `.venv\Scripts\activate`.

## 1. Base de datos sin usar `psql`

Si la base de datos `library_classifier_db` y sus tablas ya fueron preparadas anteriormente, no ejecutes ningun comando de PostgreSQL. Continua directamente con la seccion 2 y configura el `.env` con las credenciales que ya utilizas.

Si PostgreSQL esta instalado pero `psql` no aparece en CMD, usa **pgAdmin**:

1. Abre pgAdmin y conecta al servidor local.
2. Crea o selecciona la base `library_classifier_db`.
3. Abre `Tools > Query Tool` para esa base.
4. Abre y ejecuta primero `data/library_schema.sql`.
5. Abre y ejecuta despues `data/login_schema.sql`.
6. Usa en `.env` el usuario, contrasena, host y puerto que ya configuraste en PostgreSQL.

No necesitas escribir `psql`, agregar PostgreSQL al `PATH` ni ejecutar comandos SQL desde CMD.

Si no existe ningun servidor PostgreSQL encendido, el login no puede consultar usuarios ni sesiones: activar `.venv` no reemplaza la base de datos. En ese caso inicia el servicio PostgreSQL desde `services.msc` o desde pgAdmin antes de levantar Flask. Sin una base disponible solo podras ejecutar las pruebas automatizadas, no demostrar los endpoints conectados a PostgreSQL.

Configura las mismas credenciales en un archivo `.env` dentro de `proyecto_bien`:

```env
DB_HOST=127.0.0.1
DB_PORT=5433
DB_NAME=library_classifier_db
DB_USER=library_classifier_user
DB_PASSWORD=cambia-esta-clave
DB_SCHEMA=library
LOGIN_SECRET_KEY=una-clave-larga-y-aleatoria
LOGIN_HOST=127.0.0.1
LOGIN_PORT=5000
SMTP_HOST=127.0.0.1
SMTP_PORT=25
SMTP_FROM=info@localhost
SMTP_STARTTLS=false
LOGIN_VERIFICATION_URL=http://127.0.0.1:5000/verify-email
LOGIN_EMAIL_MODE=console
```

`LOGIN_EMAIL_MODE=console` es el modo local para Windows: no usa Postfix, no usa SMTP y no requiere configurar ningun proveedor externo. Despues de un registro, el enlace de verificacion aparece en la ventana de CMD donde esta corriendo Flask. Para produccion elimina esa variable o usa `LOGIN_EMAIL_MODE=smtp` y configura Postfix.

## 2. Crear las tablas sin `psql`

El error `psycopg.errors.UndefinedTable: relation "library.users" does not exist` significa que PostgreSQL esta funcionando, pero aun no se ha ejecutado el esquema del login. Desde **CMD**, en la raiz de `proyecto_bien`, ejecuta exactamente:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
.venv\Scripts\python.exe -c "import psycopg; from pathlib import Path; from apps.services.login.config import Settings; s=Settings.from_env(); sql=Path('data/login_schema.sql').read_text(encoding='utf-8'); c=psycopg.connect(**s.db_config); c.execute(sql); c.commit(); print('LOGIN_SCHEMA_OK'); c.close()"
```

Debes ver:

```text
LOGIN_SCHEMA_OK
```

Este comando crea `library.users` y `library.auth_sessions` usando la misma configuracion del `.env`. Es idempotente: puedes ejecutarlo otra vez sin borrar usuarios ni sesiones existentes. No usa `psql`, pgAdmin ni comandos externos de PostgreSQL.

## 3. Correo local sin Postfix

Para obtener evidencias en Windows usa `LOGIN_EMAIL_MODE=console` como se muestra arriba. No necesitas CAPTCHA: CAPTCHA solo demuestra que quien envia la solicitud es una persona y no verifica la propiedad del correo. El modo console conserva el flujo de token y `/verify-email`, pero muestra el enlace localmente para poder probarlo desde CMD.

## 4. Preparar Postfix local (opcional)

Postfix no se instala como servicio nativo de Windows. Ejecutalo en la instancia Linux o contenedor administrado por el proyecto, escuchando en el puerto 25 de la maquina visible por Flask. Configura `myhostname`, `myorigin`, `mydestination` y `inet_interfaces` para el dominio que controles. Usa `info@localhost` solo para la demostracion local; para entrega real cambia `SMTP_FROM` a una cuenta del dominio propio, publica DNS `A` y `MX`, y configura SPF, DKIM y DMARC.

Comprueba que la instancia responde antes de levantar Flask:

```cmd
netstat -ano | findstr :25
```

El mensaje de verificacion debe llegar a una cuenta real mediante la propia instancia Postfix. No configures servidores SMTP de Google u Outlook.

## 5. Activar el entorno e instalar

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r apps\services\login\requirements.txt
```

Si `.venv` no existe, crealo una sola vez y vuelve a activar:

```cmd
py -m venv .venv
.venv\Scripts\activate
```

## 6. Levantar el login

En la misma terminal:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.login.app
```

Debe quedar escuchando en `http://127.0.0.1:5000`. La documentacion se consulta en `http://127.0.0.1:5000/docs` y el contrato en `http://127.0.0.1:5000/openapi.yaml`.

Si Flask ya estaba abierto antes de agregar `LOGIN_EMAIL_MODE=console`, presiona `Ctrl+C` en esa ventana y levantalo otra vez. Las variables del `.env` se leen al iniciar Flask, no en cada solicitud.

Si el primer registro devolvio `500`, PostgreSQL pudo haber guardado el usuario antes de que fallara el envio SMTP. En ese caso usa otro correo para la evidencia, por ejemplo `ana2@example.com`. Si recibes `409`, significa que ese correo ya existe y debes usar otro.

## 7. Capturas de cada endpoint

Abre otra ventana de CMD. Cada comando imprime el cuerpo que debes capturar como evidencia.

```cmd
curl.exe -i "http://127.0.0.1:5000/health"
curl.exe -i "http://127.0.0.1:5000/health?format=json"
```

Guarda las cookies para probar la sesion completa:

```cmd
curl.exe -i -c cookies.txt -X POST "http://127.0.0.1:5000/register?format=json" -H "Content-Type: application/json" -d "{\"nombre\":\"Ana\",\"apellido_paterno\":\"Lopez\",\"apellido_materno\":\"Diaz\",\"email\":\"ana2@example.com\",\"password\":\"Correcta123!\"}"
```

Como tienes `LOGIN_EMAIL_MODE=console`, copia el enlace que aparece en la ventana de CMD donde ejecutaste Flask. Extrae el valor que aparece despues de `token=` y ejecuta:

```cmd
curl.exe -i "http://127.0.0.1:5000/verify-email?token=PEGA_AQUI_EL_TOKEN&format=json"
curl.exe -i -b cookies.txt -c cookies.txt -X POST "http://127.0.0.1:5000/login?format=json" -H "Content-Type: application/json" -d "{\"email\":\"ana2@example.com\",\"password\":\"Correcta123!\"}"
curl.exe -i -b cookies.txt "http://127.0.0.1:5000/session?format=json"
curl.exe -i -b cookies.txt -X POST "http://127.0.0.1:5000/logout?format=json"
curl.exe -i -b cookies.txt "http://127.0.0.1:5000/session?format=json"
```

Prueba tambien errores y XML predeterminado:

```cmd
curl.exe -i -X POST "http://127.0.0.1:5000/register" -H "Content-Type: application/json" -d "{\"nombre\":\"Ana\",\"apellido_paterno\":\"Lopez\",\"apellido_materno\":\"Diaz\",\"email\":\"correo-invalido\",\"password\":\"123\"}"
curl.exe -i -X POST "http://127.0.0.1:5000/login?format=json" -H "Content-Type: application/json" -d "{\"email\":\"ana2@example.com\",\"password\":\"incorrecta\"}"
```

## 8. Prueba del monorepo y Electron-app

El login no cambia el catalogo. En otra terminal, desde `proyecto_bien`, ejecuta el servicio SOAP en su puerto original:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

En otra terminal prueba el catalogo y despues Electron:

```cmd
curl.exe -i "http://127.0.0.1:5001/books?format=json"
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

La evidencia del monorepo debe mostrar simultaneamente el login en `5000`, el catalogo en `5001`, las respuestas JSON/XML y Electron consumiendo `/books`. Para pruebas automatizadas:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m pytest apps\services\login\tests apps\services\soap\tests -q
```

## 9. Evidencias desde Postman

Usa Postman para obtener una captura de cada respuesta. Antes de comenzar, verifica lo siguiente:

1. PostgreSQL esta activo en el puerto `5433`.
2. Las tablas `library.users` y `library.auth_sessions` ya fueron creadas.
3. Flask esta levantado en `http://127.0.0.1:5000`.
4. En el archivo `.env` esta configurado `LOGIN_EMAIL_MODE=console`.
5. Postman conserva las cookies. En Postman puedes revisar el icono de cookies de la solicitud o la opcion `Cookies` junto a la barra de URL. No borres la cookie de `127.0.0.1` entre `/login`, `/session` y `/logout`.

En todas las solicitudes que regresan JSON agrega el parametro `?format=json` y el header:

```text
Content-Type: application/json
```

### 9.1 GET `/health`

1. Crea una solicitud nueva en Postman.
2. Selecciona metodo `GET`.
3. Usa la URL:

```text
http://127.0.0.1:5000/health?format=json
```

4. No agregues Body.
5. Presiona `Send`.
6. Toma una captura donde se vean la URL, el estado `200 OK` y el JSON recibido.

Respuesta esperada:

```json
{
	"service": "library-login",
	"status": "ok"
}
```

Esta respuesta confirma que Flask puede consultar PostgreSQL.

### 9.2 POST `/register`

1. Crea otra solicitud.
2. Selecciona metodo `POST`.
3. Usa la URL:

```text
http://127.0.0.1:5000/register?format=json
```

4. En `Headers` agrega `Content-Type` con valor `application/json`.
5. En `Body`, selecciona `raw` y despues `JSON`.
6. Pega este JSON. Usa un correo diferente si ya registraste `ana3@example.com`:

```json
{
	"nombre": "Ana",
	"apellido_paterno": "Lopez",
	"apellido_materno": "Diaz",
	"email": "postman@example.com",
	"password": "Correcta123!"
}
```

7. Presiona `Send`.
8. Toma una captura del estado `201 Created` y del JSON de respuesta.
9. En la ventana de CMD donde corre Flask copia el enlace que inicia con `http://127.0.0.1:5000/verify-email`. Ese enlace contiene el token necesario para activar el correo antes de probar `/login`.

Respuesta esperada, sin mostrar nunca la contraseña:

```json
{
	"user_id": 3,
	"first_name": "Ana",
	"last_name": "Lopez",
	"maternal_last_name": "Diaz",
	"email": "postman@example.com",
	"email_verified": false,
	"email_verification_required": true,
	"links": [
		{"rel": "self", "href": "/register"},
		{"rel": "login", "href": "/login"}
	]
}
```

### 9.3 Activar la cuenta antes de `/login`

El login rechaza usuarios cuyo correo no esta verificado. Como el modo local es `console`, no necesitas Postfix.

1. Crea una solicitud `GET`.
2. Pega el enlace mostrado en CMD, por ejemplo:

```text
http://127.0.0.1:5000/verify-email?token=PEGA_AQUI_EL_TOKEN&format=json
```

3. Presiona `Send`.
4. Toma una captura del estado `200 OK` y del JSON donde aparezca `"email_verified": true`.

### 9.4 POST `/login`

1. Crea una solicitud nueva.
2. Selecciona metodo `POST`.
3. Usa la URL:

```text
http://127.0.0.1:5000/login?format=json
```

4. En `Headers` agrega `Content-Type: application/json`.
5. En `Body > raw > JSON` pega:

```json
{
	"email": "postman@example.com",
	"password": "Correcta123!"
}
```

6. Presiona `Send`.
7. Postman debe guardar automaticamente la cookie de sesion para `127.0.0.1`.
8. Toma una captura del estado `200 OK`, el mensaje `Sesion iniciada`, el usuario y `expires_at`. Nunca fotografies ni compartas contraseñas.

Respuesta esperada:

```json
{
	"message": "Sesion iniciada.",
	"user": {
		"user_id": 3,
		"first_name": "Ana",
		"last_name": "Lopez",
		"maternal_last_name": "Diaz",
		"email": "postman@example.com"
	},
	"expires_at": "2026-09-21T...+00:00",
	"links": [
		{"rel": "self", "href": "/session"},
		{"rel": "logout", "href": "/logout"}
	]
}
```

### 9.5 GET `/session`

1. Crea una solicitud `GET`.
2. Usa la URL:

```text
http://127.0.0.1:5000/session?format=json
```

3. No agregues Body ni token manual. Postman debe enviar la cookie guardada despues de `/login`.
4. Presiona `Send`.
5. Toma una captura del estado `200 OK` y de `"authenticated": true`.

Respuesta esperada:

```json
{
	"authenticated": true,
	"user": {
		"user_id": 3,
		"first_name": "Ana",
		"last_name": "Lopez",
		"maternal_last_name": "Diaz",
		"email": "postman@example.com",
		"email_verified": true
	},
	"links": [
		{"rel": "self", "href": "/session"},
		{"rel": "logout", "href": "/logout"}
	]
}
```

### 9.6 POST `/logout`

1. Crea una solicitud `POST`.
2. Usa la URL:

```text
http://127.0.0.1:5000/logout?format=json
```

3. No agregues Body. Conserva la cookie que Postman obtuvo en `/login`.
4. Presiona `Send`.
5. Toma una captura del estado `200 OK` y del mensaje `Sesion cerrada`.

Respuesta esperada:

```json
{
	"message": "Sesion cerrada.",
	"links": [
		{"rel": "login", "href": "/login"}
	]
}
```

### 9.7 Comprobar que `/logout` funciono

Vuelve a ejecutar la solicitud `GET /session?format=json` sin borrar manualmente la cookie. Debe regresar `401 Unauthorized` con un error similar a:

```json
{
	"error": "No existe una sesion autenticada.",
	"status": 401
}
```

Toma esta captura como evidencia de que `/logout` revoco la sesion. El orden recomendado de capturas es: `health`, `register`, `verify-email`, `login`, `session`, `logout` y `session` nuevamente con `401`.
