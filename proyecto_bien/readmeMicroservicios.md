# README de microservicios - Proyecto Bien

Este documento te indica cómo correr todos los microservicios del proyecto desde CMD de Windows sin depender de PostgreSQL ni de un gestor visual. La solución está preparada para funcionar con almacenamiento en memoria y caché Redis opcional. Los servicios ya integrados en esta carpeta son:

1. Login
2. Books / SOAP
3. Users
4. Authors
5. Orders
6. Payments

> En este proyecto, todos los servicios comparten la misma clave JWT configurada en variables de entorno, y la caché Redis se usa solo para lecturas frecuentes del catálogo.

---

## 1. Requisitos previos

Necesitas:

- Python 3.11+
- Git (opcional)
- CMD o PowerShell
- WSL2 con Ubuntu si quieres usar Redis real desde Windows (opcional, recomendado)
- Node.js si ejecutas la app Electron (opcional)

Verifica que Python esté disponible:

```cmd
python --version
```

Si no está en PATH, reinstálalo y abre otra terminal.

---

## 2. Abrir la carpeta del proyecto

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
```

---

## 3. Crear entorno virtual y instalar dependencias

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si `redis` no aparece instalado, puedes instalarlo explícitamente:

```cmd
python -m pip install redis
```

---

## 4. Configurar variables de entorno

La carpeta ya incluye un archivo `.env` con las claves necesarias. Asegúrate de que contenga algo como esto:

```env
JWT_SECRET_KEY=project-bien-secret
LOGIN_SECRET_KEY=project-bien-secret
REDIS_URL=redis://localhost:6379/0
```

Si cambias la clave, usa la misma en todos los servicios para que los JWT se validen correctamente.

---

## 5. Iniciar Redis (recomendado)

Desde CMD de Windows:

```cmd
wsl -d Ubuntu -- sudo service redis-server start
wsl -d Ubuntu -- redis-cli ping
```

La respuesta esperada es:

```text
PONG
```

Si Redis no está disponible, la app sigue funcionando en modo sin caché, pero no se usará la cache Redis.

---

## 6. Ejecutar los microservicios

Abre una terminal por servicio. En cada una, activa el entorno virtual y ejecuta el servicio.

### 6.1 Login

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.login.app
```

Debe quedar en:

```text
http://127.0.0.1:5000
```

### 6.2 SOAP / Books

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

Debe quedar en:

```text
http://127.0.0.1:5001
```

### 6.3 Users

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.users.app
```

Debe quedar en:

```text
http://127.0.0.1:5005
```

### 6.4 Authors

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.authors.app
```

Debe quedar en:

```text
http://127.0.0.1:5006
```

### 6.5 Orders

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.orders.app
```

Debe quedar en:

```text
http://127.0.0.1:5007
```

### 6.6 Payments

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.payments.app
```

Debe quedar en:

```text
http://127.0.0.1:5008
```

---

## 7. Validar el login JWT

Desde PowerShell o CMD:

```cmd
curl -X POST http://127.0.0.1:5000/register?format=json -H "Content-Type: application/json" -d "{\"nombre\":\"Ana\",\"apellido_paterno\":\"Lopez\",\"apellido_materno\":\"Diaz\",\"email\":\"ana@example.com\",\"password\":\"Correcta123!\"}"
```

Luego verifica el correo con el token devuelto y ejecuta login:
Luego verifica el correo usando el token del enlace que apareció en la terminal de Login y ejecuta login:

Como `LOGIN_EMAIL_MODE=console`, el enlace de verificación aparece en la terminal donde corre Login, no en el JSON de registro. Copia de ese enlace el valor que sigue a `token=`.

```cmd
curl -X GET "http://127.0.0.1:5000/verify-email?token=TU_TOKEN_AQUI&format=json"
curl -X POST http://127.0.0.1:5000/login?format=json -H "Content-Type: application/json" -d "{\"email\":\"ana@example.com\",\"password\":\"Correcta123!\"}"
```

Debe devolver un JSON con `token`, `token_type` y `expires_in`. El JWT debe firmarse con HS256 y contener `user_id`, `email` y otros claims básicos.

---

## 8. Probar los servicios protegidos por JWT

### 8.1 Users

```cmd
curl http://127.0.0.1:5005/users
```

Sin token devuelve 401. Con token:

```cmd
curl http://127.0.0.1:5005/users -H "Authorization: Bearer <JWT>"
```

### 8.2 Authors

```cmd
curl http://127.0.0.1:5006/authors
curl -X POST http://127.0.0.1:5006/authors -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"name\":\"Gabriel García Márquez\",\"country\":\"Colombia\"}"
```

### 8.3 Orders

```cmd
curl -X POST http://127.0.0.1:5007/orders -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"customer_name\":\"Carlos\",\"items\":[{\"book_isbn\":\"9781234567890\",\"quantity\":2,\"price\":150}],\"status\":\"pending\"}"
```

### 8.4 Payments

```cmd
curl -X POST http://127.0.0.1:5008/payments -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"order_id\":1,\"amount\":300,\"method\":\"card\"}"
```

---

## 9. Probar el catálogo SOAP

```cmd
curl http://127.0.0.1:5001/books
curl "http://127.0.0.1:5001/books?format=json"
```

Debe devolver XML por defecto y JSON cuando se pide `format=json`.

Si quieres revisar la documentación Swagger:

```cmd
http://127.0.0.1:5001/docs/
```

---

## 10. Script rápido para arrancar todo en CMD

Puedes guardar este bloque como `run_all_services.cmd` en la carpeta del proyecto:

```cmd
@echo off
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
call .venv\Scripts\activate
start "Login" python -m apps.services.login.app
start "SOAP" python -m apps.services.soap.app
start "Users" python -m apps.services.users.app
start "Authors" python -m apps.services.authors.app
start "Orders" python -m apps.services.orders.app
start "Payments" python -m apps.services.payments.app
```

Después de ejecutar el script, abre cada URL con el navegador o `curl` para comprobar que responde.

---

## 11. Evidencias recomendadas

### Evidencia 1: Redis disponible

- Script:

```cmd
wsl -d Ubuntu -- redis-cli ping
```

- Esperado: `PONG`
- Qué demuestra: Redis está corriendo y listo para caché.

### Evidencia 2: Login crea usuario y genera JWT

- Script:

```cmd
curl -X POST http://127.0.0.1:5000/register?format=json -H "Content-Type: application/json" -d "{\"nombre\":\"Lucia\",\"apellido_paterno\":\"Mendoza\",\"apellido_materno\":\"Rojas\",\"email\":\"lucia.mendoza.evidencia.20261005@example.com\",\"password\":\"CieloNaranja2026!\"}"
```

- Esperado: código 201 y un JSON con `email_verification_required`. El enlace de verificación se imprime en la terminal donde corre Login; guarda el valor que aparece después de `token=`.
- Qué demuestra: el registro del servicio login funciona.

### Evidencia 3: Verificación de correo y login

- Script:

Reemplaza `PEGA_EL_TOKEN_DE_LA_TERMINAL_DE_LOGIN` por el valor que aparece después de `token=` en el enlace impreso en la terminal de Login. No viene en el JSON del registro. Si esa terminal se cerró o el correo ya fue registrado, usa un correo nuevo en la evidencia 2 y copia el enlace recién impreso. Ejecuta el login solo después de que la verificación responda 200.

```cmd
curl -X GET "http://127.0.0.1:5000/verify-email?format=json&token=PEGA_EL_TOKEN_DE_LA_TERMINAL_DE_LOGIN"
curl -X POST http://127.0.0.1:5000/login?format=json -H "Content-Type: application/json" -d "{\"email\":\"lucia.mendoza.evidencia.20261005@example.com\",\"password\":\"CieloNaranja2026!\"}"
```

- Esperado: la verificación responde 200 y luego el login responde 200 con JWT en `token`.
- Qué demuestra: el servicio valida credenciales, firma JWT y devuelve sesión válida.

### Evidencia 4: Ruta protegida sin token responde 401

- Script:

```cmd
curl -i http://127.0.0.1:5005/users
```

- Esperado: `401 Unauthorized`.
- Qué demuestra: la API protege escrituras y listados con JWT.

### Evidencia 5: Autor creado con permiso correcto

- Script:

```cmd
curl -X POST http://127.0.0.1:5006/authors -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"name\":\"Gabriel García Márquez\",\"country\":\"Colombia\"}"
```

- Esperado: 201 Created y JSON con el autor recién creado.
- Qué demuestra: la validación de roles y permisos funciona.

### Evidencia 6: Pedido creado y consultado

- Script:

```cmd
curl -X POST http://127.0.0.1:5007/orders -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"customer_name\":\"Carlos\",\"items\":[{\"book_isbn\":\"9781234567890\",\"quantity\":2,\"price\":150}],\"status\":\"pending\"}"
curl -H "Authorization: Bearer <JWT>" http://127.0.0.1:5007/orders
```

- Esperado: status `pending` en la respuesta del pedido.
- Qué demuestra: la gestión de pedidos, líneas y estado funciona.

### Evidencia 7: Pago registra y actualiza estado del pedido

- Script:

```cmd
curl -X POST http://127.0.0.1:5008/payments -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\"order_id\":1,\"amount\":300,\"method\":\"card\"}"
```

- Esperado: 201 y `status: "paid"`.
- Qué demuestra: el pago actualiza el pedido a pagado.

### Evidencia 8: Catálogo SOAP responde en XML y JSON

- Script:

```cmd
curl http://127.0.0.1:5001/books
curl "http://127.0.0.1:5001/books?format=json"
```

- Esperado: XML por defecto y JSON cuando se usa `format=json`.
- Qué demuestra: el servicio de catálogo sigue funcionando y se integra con la API previa del proyecto.

### Evidencia 9: Prueba automatizada del proyecto

- Script:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m pytest apps\services\login\tests apps\services\soap\tests apps\services\test_microservices.py -q
```

- Esperado: `15 passed`.
- Qué demuestra: el conjunto completo del proyecto actual no tiene regresiones.

---

## 12. Recomendaciones finales

- Nunca guardes secretos hardcodeados en el código. Usa `.env` y variables de entorno.
- Mantén `JWT_SECRET_KEY` igual en todos los servicios.
- Para producción, habilita HTTPS y restringe CORS a tus dominios autorizados.
- Si quieres llevar esto a un entorno real, puedes migrar la data en memoria a PostgreSQL o Redis persistente, pero la base de esta entrega ya funciona sin PSQL.

Con estos pasos ya puedes ejecutar el proyecto completo desde CMD sin consultar nada más y validar cada pieza del flujo actual.
