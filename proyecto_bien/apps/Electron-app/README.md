# Electron App - Catálogo de libros XML

Esta aplicación de escritorio construida con Electron consume el servicio XML del catálogo disponible en el microservicio `library_soap_gsm` y presenta los libros en tarjetas responsivas con paginación, diseño Material y configuración persistente del endpoint.

## Requisitos previos

- Windows 11
- Node.js 18 o superior
- npm
- Acceso al servicio del microservicio en `http://127.0.0.1:5001/books`

## 1) Instalar Node.js en Windows 11

1. Abre el navegador y descarga Node.js LTS desde:
   https://nodejs.org/
2. Ejecuta el instalador `.msi` o `.exe`.
3. Acepta los términos y deja la configuración por defecto.
4. Cuando termine la instalación, abre `PowerShell` o `CMD`.
5. Verifica la instalación:

```powershell
node -v
npm -v
```

Si ambos comandos responden con versiones, la instalación fue correcta.

## 2) Instalar Electron localmente

Desde la carpeta de la app:

```powershell
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
```

Este comando crea la carpeta `node_modules` y descarga Electron.

## 3) Ejecutar la aplicación

Para iniciar la app:

```powershell
npm start
```

La ventana principal mostrará los libros desde el XML del servicio identificado en la configuración.

## 4) Cambiar la IP o endpoint del servicio

Dentro de la aplicación, presiona el botón:

- `Configurar servicio`

Se abrirá un popup para ingresar:

- IP/host del microservicio, por ejemplo: `http://127.0.0.1:5001`
- Endpoint, por ejemplo: `/books`

Al guardar, la configuración queda persistida en `LocalStorage` del navegador embebido de Electron. La próxima vez que abras la app, se reutiliza la misma URL.

## 5) Requisitos del servicio backend

Asegúrate de que el microservicio esté levantado y responda en XML en esta ruta:

```text
http://127.0.0.1:5001/books
```

Ejemplo esperado:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<library>
  <book>
    <isbn>978... </isbn>
    <title>...</title>
    <author>...</author>
    <imageUrl>...</imageUrl>
    <price>...</price>
  </book>
</library>
```

## 6) Solución de problemas comunes

### Error: `electron: not found`

Ejecuta:

```powershell
npm install
```

### La app carga pero no muestra libros

Revisa que el servicio esté activo:

```powershell
curl http://127.0.0.1:5001/books
```

Si usas PowerShell, prueba:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/books
```

### Quiero cambiar la URL manualmente

Puedes editar la configuración en la UI o borrar el valor almacenado en LocalStorage si es necesario.

## Estructura de la app

```text
Electron-app/
├── main.js
├── preload.js
├── index.html
├── styles.css
├── package.json
├── README.md
```

## Funcionalidades implementadas

- Consumo del servicio XML del backend
- Mostrar 6 tarjetas por página
- Paginación
- Diseño responsive con tarjetas tipo material
- Botón para cambiar host + endpoint
- Persistencia con LocalStorage

---

## Actualizar datos del microservicio y ejecutar desde CMD Windows

Para actualizar los datos del catálogo o volver a conectar la app, sigue estos pasos:

1. Abre `CMD` o `PowerShell` en la carpeta del proyecto.
2. Levanta el microservicio si no está activo:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
python app.py
```

3. En otra ventana del terminal, entra a la app Electron:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

4. Si el endpoint cambia, abre `Configurar servicio` y guarda la nueva URL.
5. La app mostrará los datos actualizados desde el backend XML.

> Nota: si el servicio cambia de IP o puerto, solo tienes que actualizar el valor desde la configuracion interna de la app o desde `LocalStorage`.

---

## Solución final si aparece `Sin conexión` o `Failed to connect`

Este error no viene de Electron, sino de que la app desktop intenta consultar el backend y el servicio no está respondiendo en `http://127.0.0.1:5001/books`.

### Paso 1: levantar el backend del proyecto

Abre una terminal en CMD o PowerShell y ejecuta esto:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python app.py
```

Si no aparece ningún error, el backend se está levantando en:

```text
http://127.0.0.1:5001
```

### Paso 2: verificar que el servicio responde

En otra terminal ejecuta:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/books
```

O bien:

```cmd
curl http://127.0.0.1:5001/books
```

Si recibes XML (no un error de conexión), entonces el backend está bien.

### Paso 3: si falla por PostgreSQL o base de datos

El servicio necesita PostgreSQL activo porque el proyecto usa la base `library_classifier_db` configurada en `.env`.

Revisa esto:

- `.env` tiene el host, puerto, usuario y contraseña correctos.
- PostgreSQL está iniciado en Windows.
- El puerto configurado es el correcto (`5433` según el proyecto).
- La base de datos existe.

Si la base de datos aún no está creada, hay que ejecutarlos scripts SQL del proyecto:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
```

Luego crea la base y ejecuta los scripts indicados en:

- `database/README.md`
- `data/library_schema.sql`
- `database/library_seed.sql`

### Paso 4: volver a configurar la app Electron

Cuando el backend ya esté funcionando:

1. Abre la app Electron.
2. Haz clic en `Configurar servicio`.
3. Escribe:
   - IP / host: `http://127.0.0.1:5001`
   - Endpoint: `/books`
4. Guarda.

### Paso 5: reiniciar la app

Después de guardar, cierra y vuelve a abrir la aplicación:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm start
```

---

## ✅ Orden correcto para no fallar

1. Activar venv
2. Instalar `psycopg[binary,pool]`
3. Verificar PostgreSQL client/libpq
4. Arrancar backend
5. Probar `http://127.0.0.1:5001/books`
6. Arrancar Electron

Ejecuta esto en orden:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --upgrade --force-reinstall "psycopg[binary,pool]"
```

Verifica que el cliente PostgreSQL/libpq esté disponible en Windows:

```cmd
where libpq.dll
```

Si aparece una ruta, el cliente está disponible. Si no aparece nada, instala PostgreSQL y vuelve a probar.

Ahora levanta el backend desde la carpeta correcta:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

O, si prefieres arrancarlo desde el servicio:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\services\soap"
.venv\Scripts\activate
python app.py
```

Comprueba que responde XML:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/books
```

Si recibes XML, ya puedes abrir Electron:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm start
```

> Si aun así sigue apareciendo `Sin conexión`, entonces la falla está en el backend o en la base de datos, no en la interfaz Electron.
