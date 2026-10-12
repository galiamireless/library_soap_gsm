# Ollama + Electron: guía completa para usar DeepSeek con el catálogo de libros

## Objetivo

Integrar una nueva vista en la app Electron del proyecto para consultar el catálogo de libros desde el backend XML y hacer preguntas a DeepSeek usando Ollama localmente, sin depender de PostgreSQL ni de `psql` si no los tienes instalados en tu máquina.

Este proyecto ya tiene la parte visual del catálogo en:

- `proyecto_bien/apps/Electron-app/index.html`
- `proyecto_bien/apps/Electron-app/main.js`
- `proyecto_bien/apps/Electron-app/package.json`

La idea es: mantener la vista del catálogo actual, añadir una nueva vista o panel con chatbot, y enviar el listado de libros como contexto a DeepSeek para responder preguntas como:

- "¿Qué libro me recomiendas para empezar?"
- "¿Cuáles son los libros más baratos?"
- "Muéstrame los títulos de tecnología y ciencia ficción que venden este catálogo"

---

## 1. Requisitos previos

Necesitas:

- Windows 10/11
- Python 3.10+ o 3.11+
- Node.js 18+
- npm
- Git opcional
- Docker Desktop instalado y en ejecución

No necesitas `psql` para esta parte si solo vas a correr la app Electron y consultar el catálogo ya disponible en XML o desde un backend que ya esté levantado.

> Importante: `psql` es solo una herramienta para administrar PostgreSQL. Si el catálogo ya está funcionando en `http://127.0.0.1:5001/books`, no necesitas PostgreSQL para ver la interfaz ni para probar DeepSeek.

---

## 2. Instalar Node.js y preparar Electron

### 2.1 Instalar Node.js

Desde CMD o PowerShell ejecuta:

```cmd
node -v
npm -v
```

Si no aparecen versiones, descarga Node.js LTS desde:

https://nodejs.org/

### 2.2 Entrar a la carpeta de Electron

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
```

Esto crea la carpeta `node_modules` con Electron.

### 2.3 Ejecutar la app desde CMD

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm start
```

Si todo va bien, se abre la ventana desktop de Electron con el catálogo.

---

## 3. Levantar el backend del catálogo sin usar PostgreSQL

Si tu catálogo ya está listo y disponible por HTTP/XML, la ruta correcta para el servicio SOAP de este proyecto es `proyecto_bien`, y el arranque debe hacerse con el módulo del servicio, no con un `app.py` que no existe ahí:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

> La configuración del servicio lee el `.env` de `proyecto_bien` y usa el puerto `5001`, no el `5000` por defecto del backend raíz.

Luego verifica:

```cmd
curl http://127.0.0.1:5001/books
```

o en PowerShell:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/books
```

La respuesta debe ser XML con los libros.

### Si no tienes PostgreSQL

No pasa nada para esta vista. Puedes seguir con la app si ya tienes:

- el servicio levantado
- la respuesta XML del catálogo disponible
- la interfaz Electron corriendo

Si el catálogo se sirve desde un JSON o XML estático, también funciona sin tocar `psql`.

---

## 4. Instalar Ollama y DeepSeek

### 4.1 Verificar Docker Desktop

```cmd
docker --version
docker info
```

`docker info` debe mostrar información del servidor Docker. Si indica que no puede conectarse, abre Docker Desktop y espera a que termine de iniciar.

### 4.3 Arrancar el servicio de Ollama

Descarga la imagen y crea el contenedor con almacenamiento persistente para el modelo:

```cmd
docker pull ollama/ollama:latest
docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama:latest
```

Esto deja un servidor local en:

```text
http://127.0.0.1:11434
```

Si el contenedor ya existe, puedes arrancarlo con:

```cmd
docker start ollama
```

### 4.4 Verificar modelos disponibles

Revisa los modelos desde el contenedor:

```cmd
docker exec -it ollama ollama list
```

### 4.5 Modelo recomendado para esta implementación

La app ya está preparada para consultar el modelo:

```text
deepseek-coder:latest
```

Si aún no lo tienes descargado, usa desde Docker:

```cmd
docker exec -it ollama ollama pull deepseek-coder:latest
```

También puedes usar modelos más ligeros si tu equipo tiene poca RAM:

```cmd
docker exec -it ollama ollama pull deepseek-r1:1.5b
```

> En esta implementación, el código de Electron usa `deepseek-coder:latest` porque ya lo tienes disponible en tu entorno y funciona bien para responder recomendaciones del catálogo.

---

## 5. Probar que Ollama funciona

En otra terminal ejecuta:

```cmd
curl http://127.0.0.1:11434/api/tags
```

o si usas Docker:

```cmd
docker exec -it ollama curl http://127.0.0.1:11434/api/tags
```

También puedes probar desde la terminal del modelo:

```cmd
docker exec -it ollama ollama run deepseek-coder:latest
```

Y ahí escribe un mensaje de prueba:

```text
Hola, dime si este modelo está funcionando correctamente.
```

Si responde, ya tienes listo DeepSeek localmente.

---

## 6. Vista de curaduría en Electron

La vista ya está implementada. Abre Electron y selecciona la pestaña **Asistente IA** en la barra que está debajo del encabezado. También puedes usar el botón **Asistente IA** de la parte superior.

La pantalla ofrece búsquedas temáticas para empezar, encontrar libros económicos, explorar IA y ciencia de datos o elegir un regalo. También permite escribir una consulta propia. DeepSeek devuelve una selección visual de libros con portada, título, autor, precio, disponibilidad y el motivo de recomendación; las fichas solo se crean para títulos que existen en el catálogo cargado.

### 6.1 Cómo se pasa el catálogo como contexto

Antes de consultar DeepSeek, conviertes los libros a texto:

```javascript
const catalogText = allBooks.map((book) => {
  return `${book.title} - ${book.author} - ISBN: ${book.isbn} - Precio: $${book.price} - Stock: ${book.stock}`;
}).join('\n');
```

Esto permite que DeepSeek compare títulos, autores, precios y stock. La respuesta se solicita en JSON para poder mostrarla como fichas en la interfaz, en lugar de una conversación de burbujas.

---

## 7. Ejemplo de uso con DeepSeek

### Pregunta de ejemplo

```text
¿Me recomiendas 3 libros del catálogo para alguien que le gusta la tecnología y la inteligencia artificial? Muestra solo el nombre, autor y precio.
```

### Prompt enviado a Ollama

```text
Usa solo este catálogo de libros y responde en español.

CATALOGO:
Clean Code - Robert C. Martin - ISBN: 9780132350884 - Precio: $350.00 - Stock: 10
The Pragmatic Programmer - Andrew Hunt - Precio: $320.00
Deep Learning - Ian Goodfellow - Precio: $480.00

PREGUNTA:
¿Me recomiendas 3 libros del catálogo para alguien que le gusta la tecnología y la inteligencia artificial? Muestra solo el nombre, autor y precio.
```

### Respuesta esperada

```text
Estos son 3 libros recomendados:

1. Clean Code - Robert C. Martin - $350.00
2. The Pragmatic Programmer - Andrew Hunt - $320.00
3. Deep Learning - Ian Goodfellow - $480.00

Si te interesa IA y software profesional, Clean Code y The Pragmatic Programmer son excelentes puntos de partida.
```

---

## 8. Flujo final recomendado para correr todo desde CMD

### Terminal 1: levantar backend del catálogo

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

### Terminal 2: arrancar Ollama

Si usas Docker (recomendado si `ollama` no está instalado localmente):

```cmd
docker pull ollama/ollama:latest
docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama:latest
```

Si el contenedor ya está creado:

```cmd
docker start ollama
```

### Terminal 3: arrancar la app Electron

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

### Terminal 4: verificar que el modelo esté disponible

```cmd
docker exec -it ollama ollama list
```

Si no aparece el modelo, descárgalo:

```cmd
docker exec -it ollama ollama pull deepseek-coder:latest
```

---

## 9. Recomendaciones importantes

1. No necesitas `psql` si solo vas a consultar el catálogo ya desplegado en XML.
2. Si el backend falla por falta de PostgreSQL, revisa que existan las tablas o que la base ya haya sido creada.
3. Para una prueba rápida, usa una pregunta en español que compare títulos, precio y autor.
4. Para esta implementación concreta, el modelo recomendado es `deepseek-coder:latest` porque ya quedó integrado en la app Electron.
5. Si la UI de Electron se queda sin conectar, verifica que `http://127.0.0.1:5001/books` responda correctamente y que Ollama esté activo en `http://127.0.0.1:11434`.

---

## 10. Resumen corto

El flujo mínimo para que funcione todo es:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python -m apps.services.soap.app
```

```cmd
docker pull ollama/ollama:latest
docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama:latest
docker exec -it ollama ollama pull deepseek-coder:latest
```

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

Con esto abres la app, cargas el catálogo de libros y puedes hacer preguntas a DeepSeek local con Ollama desde la nueva vista.

---

## 11. Ejemplo final de caso de uso

Pregunta del usuario desde Electron:

```text
¿Hay libros de IA o programación en el catálogo? Muéstrame los más recomendados y cuéntame cuál es el más barato.
```

Ollama responde con una sugerencia basada en el contenido real del catálogo, ayudando al usuario a elegir un libro sin salir de la aplicación.

Esto es exactamente la integración que se busca: una app Electron con catálogo de libros y asistente inteligente usando DeepSeek + Ollama.
