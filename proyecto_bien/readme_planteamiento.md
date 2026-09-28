# README de planteamiento: JWT en login y protección de escrituras del servicio book

Este documento responde exactamente al ejercicio del prompt. La tarea no es solo documentar el proyecto, sino dejar claro que se debe proteger la escritura del catálogo con JWT emitido por el servicio de login, mantener público el catálogo de consulta y validar los tokens de forma estricta, sin aceptar `alg: none`.

Se trabaja dentro de la carpeta:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
```

---

## 1. Objetivo del ejercicio

Retomamos los microservicios de la librería en línea:

- login: register, login, logout, session, health
- book: catálogo de libros con esquema de PostgreSQL

La obligación del planteamiento es esta:

- proteger las operaciones de escritura del servicio book
- exigir un JWT válido emitido por el servicio login
- mantener públicos los GET de consulta del catálogo
- validar los tokens siempre, incluso en endpoints de login y sesión
- no usar `alg: none`
- tomar evidencias con la aplicación corriendo en segundo plano

### Reglas de negocio

- GET /api/books y GET /api/books/{isbn}: públicos, no requieren token
- POST /api/books, PUT /api/books/{isbn}, PATCH /api/books/{isbn}, DELETE /api/books/{isbn}: protegidos
- las operaciones protegidas requieren:
  - Authorization: Bearer <token>
- el token se emite desde /login, después de validar password_hash
- el servicio login debe validar el token en todas las rutas que lo necesiten
- cualquier token con algoritmo no permitido o `alg: none` debe rechazarse

---

## 2. Entorno desde cero en CMD

### 2.1 Crear entorno virtual

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

### 2.2 Instalar dependencias

```cmd
pip install -r requirements.txt
pip install -r apps\services\login\requirements.txt
pip install -r apps\services\soap\requirements.txt
```

---

## 3. Configuración del entorno local

Copia el ejemplo del proyecto:

```cmd
copy .env.example .env
```

Edítalo con tus datos reales. Debe existir la base de datos correcta para login y catálogo.

Ejemplo orientativo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=library_classifier_db
DB_USER=library_classifier_user
DB_PASSWORD=cambia-esta-clave
DB_SCHEMA=library

LOGIN_HOST=127.0.0.1
LOGIN_PORT=5000
LOGIN_SECRET_KEY=mi-clave-login-local

HOST=127.0.0.1
PORT=5001
DEBUG=false

JWT_SECRET_KEY=mi-jwt-secret-local
JWT_ALGORITHM=HS256
```

> No versionar secretos reales. El archivo `.env` debe quedarse local.

---

## 4. Crear la base de datos sin usar psql

El prompt dice explícitamente que no se usará `psql`. Por eso debe crearse la base con una herramienta visual o cliente SQL grafico.

### Opción recomendada

- pgAdmin 4
- DBeaver
- cualquier cliente PostgreSQL GUI

### Qué hacer

1. Crear la base `library_classifier_db`
2. Crear el usuario `library_classifier_user`
3. Crear el esquema `library`
4. Ejecutar los scripts SQL del proyecto
5. Confirmar que las tablas del catálogo y del login existen

No importa si se hace desde pgAdmin o desde otro cliente visual. Lo importante es que se haga sin `psql` y sin romper la base ya usada por el proyecto.

---

## 5. Levantar el servicio login

### 5.1 Arranque

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\services\login"
C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\.venv\Scripts\python.exe app.py
```

### 5.2 Verificación

```cmd
curl http://127.0.0.1:5000/health
```

Debe devolver una respuesta válida del servicio.

---

## 6. Flujo correcto de login y generación de token

### 6.1 Registrar usuario

```cmd
curl -X POST "http://127.0.0.1:5000/register?format=json" -H "Content-Type: application/json" -d "{\"nombre\":\"Ana\",\"apellido_paterno\":\"Lopez\",\"apellido_materno\":\"Diaz\",\"email\":\"ana@example.com\",\"password\":\"Correcta123!\"}"
```

### 6.2 Verificar correo

```cmd
curl "http://127.0.0.1:5000/verify-email?format=json&token=TU_TOKEN_DE_VERIFICACION"
```

### 6.3 Login con emisión de JWT

```cmd
curl -X POST "http://127.0.0.1:5000/login?format=json" -H "Content-Type: application/json" -d "{\"email\":\"ana@example.com\",\"password\":\"Correcta123!\"}"
```

Debe devolver un JWT real, por ejemplo:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 6.4 Consulta de sesión

```cmd
curl "http://127.0.0.1:5000/session?format=json" -H "Authorization: Bearer TU_TOKEN_AQUI"
```

### 6.5 Logout

```cmd
curl -X POST "http://127.0.0.1:5000/logout?format=json" -H "Authorization: Bearer TU_TOKEN_AQUI"
```

---

## 7. Levantar el servicio book

### 7.1 Arranque

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\services\soap"
C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\.venv\Scripts\python.exe app.py
```

### 7.2 Validar catálogo público

```cmd
curl "http://127.0.0.1:5001/books?format=json"
curl "http://127.0.0.1:5001/api/books?format=json"
```

> El servicio debe permitir consultar el catálogo sin token.

---

## 8. Protección de las escrituras del servicio book

### 8.1 GET público

```cmd
curl "http://127.0.0.1:5001/api/books?format=json"
curl "http://127.0.0.1:5001/api/books/9781234567890?format=json"
```

### 8.2 POST protegido

```cmd
curl -X POST "http://127.0.0.1:5001/api/books?format=json" -H "Content-Type: application/json" -H "Authorization: Bearer TU_TOKEN_AQUI" -d "{\"isbn\":\"9781234567890\",\"title\":\"Libro protegido\",\"author\":\"Autor Demo\",\"price\":150,\"stock\":10,\"publisher\":\"Editorial Demo\",\"publicationYear\":2026,\"description\":\"Libro con validacion JWT\"}"
```

### 8.3 PUT, PATCH y DELETE protegidos

```cmd
curl -X PUT "http://127.0.0.1:5001/api/books/9781234567890?format=json" -H "Content-Type: application/json" -H "Authorization: Bearer TU_TOKEN_AQUI" -d "{\"title\":\"Libro actualizado\"}"

curl -X PATCH "http://127.0.0.1:5001/api/books/9781234567890?format=json" -H "Content-Type: application/json" -H "Authorization: Bearer TU_TOKEN_AQUI" -d "{\"stock\":20}"

curl -X DELETE "http://127.0.0.1:5001/api/books/9781234567890?format=json" -H "Authorization: Bearer TU_TOKEN_AQUI"
```

### 8.4 Sin token debe fallar

```cmd
curl -X POST "http://127.0.0.1:5001/api/books?format=json" -H "Content-Type: application/json" -d "{\"isbn\":\"9781234567891\",\"title\":\"Sin token\"}"
```

El resultado esperado es 401 o 403, nunca éxito.

---

## 9. Validación estricta de tokens JWT

La validación debe hacerse siempre, y debe ser estricta.

### Requisitos obligatorios

- existir header `Authorization`
- formato correcto: `Bearer <token>`
- verificar firma del JWT
- verificar expiración
- aceptar solo algoritmos permitidos
- rechazar `alg: none`
- rechazar tokens corruptos o inválidos

### Ejemplo válido

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Ejemplo no permitido

```json
{"alg":"none","typ":"JWT"}
```

Debe rechazarse inmediatamente.

---

## 10. Evidencias que deben tomarse con la app corriendo

### Evidencia 1: login funcionando

- arrancar servicio login
- ejecutar GET /health
- registrar usuario
- hacer login
- mostrar el JWT emitido

### Evidencia 2: catálogo público

- arrancar servicio book
- ejecutar GET /api/books
- mostrar respuesta sin token

### Evidencia 3: escritura protegida

- ejecutar POST o PUT con Authorization: Bearer <token>
- mostrar que funciona

### Evidencia 4: escritura denegada

- ejecutar la misma petición sin token
- mostrar error 401 o 403

### Evidencia 5: token inválido

- enviar token corrupto o con `alg: none`
- mostrar rechazo

### Evidencia 6: Electron

- arrancar app Electron
- mostrar catálogo cargado desde el endpoint
- asegurar que la app sigue funcionando y no se rompe

---

## 11. Cuidado con monolito y Electron

Este ejercicio debe hacerse sin romper otras partes del proyecto.

- no destruir el monolito existente
- no borrar rutas ya funcionales
- no destruir la app Electron
- no romper el servicio SOAP
- añadir JWT en capas, no reemplazar bruscamente el sistema

---

## 12. Checklist final para entregar

Debe quedar documentado claramente:

- base de datos creada sin `psql`
- entorno virtual activado
- login levantado en puerto 5000
- book levantado en puerto 5001
- usuario registrado
- JWT emitido por login
- consulta pública sin token exitosa
- escritura protegida con token válido exitosa
- escritura sin token rechazada
- token inválido o con `alg: none` rechazado
- app Electron funcionando sin romper el proyecto

---

## 13. Resumen final

El planteamiento pide exactamente esto:

- trabajar en `library_soap_gsm/proyecto_bien`
- proteger las escrituras del servicio book con JWT
- mantener públicos GET /api/books y GET /api/books/{isbn}
- emitir el token desde login
- validar todos los tokens siempre
- no usar `alg: none`
- documentar todo desde CMD, sin psql
- cuidar que nada del monolito, SOAP o Electron se rompa

Si se sigue este flujo, se cumple el ejercicio tal como lo pide el prompt.