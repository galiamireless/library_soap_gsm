# Guia de ejecucion y evidencias

Servicio: `library_soap_service`  
Ruta del proyecto: `E3/Apps/library_soap_service`

## 1. Preparar la base de datos

El servicio espera PostgreSQL con las tablas de E2 (`books`, `authors`, `book_authors`, `formats`, `book_images`, `concepts`, `book_concepts`, `genres` y `book_genres`). Ejecuta primero el esquema de E2 y despues:

```sql
\i sql/soap_module.sql
```

Completa un archivo `.env` copiando `.env.example`. Usa un usuario de aplicacion con permisos de lectura sobre el catalogo y permisos de escritura sobre las tablas del modulo SOAP.

## 2. Windows CMD

Abre **CMD**, no PowerShell, y ejecuta:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\E3\Apps\library_soap_service"
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
set PYTHONPATH=.
python app.py
```

Deja esa ventana abierta. El servicio queda en `http://127.0.0.1:5000`.

En otra ventana de CMD prueba:

```cmd
curl.exe -i "http://127.0.0.1:5000/health?format=json"
curl.exe -i "http://127.0.0.1:5000/health"
curl.exe -i "http://127.0.0.1:5000/books?format=json"
curl.exe -i "http://127.0.0.1:5000/books/9780451524935?format=json"
curl.exe -i "http://127.0.0.1:5000/books/minimal?format=json"
curl.exe -i "http://127.0.0.1:5000/cloud-concepts?format=json"
```

Para detener Flask regresa a la primera ventana y presiona `Ctrl+C`.

## 3. VM de GCP

Desde CMD en Windows, entra a la VM sustituyendo los valores entre corchetes:

```cmd
gcloud compute ssh [USUARIO]@[NOMBRE_VM] --zone=[ZONA]
```

Dentro de la VM:

```bash
cd ~/library_soap_service
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
nano .env
export PYTHONPATH=.
python app.py
```

En `.env` usa `SOAP_HOST=0.0.0.0`, `SOAP_PORT=5001` y los datos reales de PostgreSQL. Para probar desde la misma VM usa:

```bash
curl -i "http://127.0.0.1:5001/health?format=json"
curl -i "http://127.0.0.1:5001/books?format=json"
curl -i "http://127.0.0.1:5001/books/9780451524935?format=json"
curl -i "http://127.0.0.1:5001/books/minimal?format=json"
curl -i "http://127.0.0.1:5001/cloud-concepts?format=json"
```

Para consultar desde el navegador se requiere una regla de firewall TCP para el puerto 5001. La URL publica queda `http://[IP_EXTERNA]:5001/books?format=json`. No expongas PostgreSQL; solo debe ser accesible por el servicio.

## 4. Que comprobar

- Sin `format`, la respuesta es XML.
- Con `format=json`, la respuesta es JSON.
- `/books/<isbn>` devuelve un libro o HTTP 404 si el ISBN no existe.
- `/books/minimal` incluye ISBN, titulo, autor e imagen.
- `/cloud-concepts` incluye IaaS, PaaS, SaaS y FaaS, junto con sus libros y definiciones.
- `/health` devuelve `status=ok` y HTTP 200 si PostgreSQL responde; si la conexion falla devuelve `status=unavailable` y HTTP 503.
- `/soap` conserva el contrato SOAP XML y su WSDL.

## 5. Como tomar screenshots

1. Ejecuta cada `curl` y deja visible la URL, el codigo HTTP, el `Content-Type` y el cuerpo.
2. En Windows presiona `Win+Shift+S`, selecciona la ventana de CMD y guarda las capturas en `evidencias/`.
3. Usa exactamente estos nombres: `01-health-json.png`, `02-health-xml.png`, `03-books-json.png`, `04-book-isbn-json.png`, `05-books-minimal-json.png`, `06-cloud-concepts-json.png`.
4. Si la prueba se hace dentro de la VM, captura la terminal SSH o abre la URL publica en el navegador y captura la respuesta.
5. Inserta las imágenes en `CLASEevidencias.md` conservando los nombres indicados.

## 6. Verificacion local sin PostgreSQL

Desde la carpeta del servicio:

```cmd
python -m py_compile app.py db\repository.py
python -m pytest -q
```

El segundo comando requiere que `pytest` este instalado y que la base de datos no sea necesaria para las pruebas unitarias.