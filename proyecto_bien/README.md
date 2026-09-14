# Proyecto Bien - Microservicio de biblioteca + Electron

Este proyecto contiene el backend del catálogo de libros en formato XML y la aplicación desktop Electron para visualizarlo.

## Estructura principal

```text
proyecto_bien/
├── .env
├── .env.example
├── README.md
├── apps/
│   ├── Electron-app/
│   └── services/
├── database/
├── data/
├── docs/
└── requirements.txt
```

## 1. Levantar el microservicio

Desde la carpeta del proyecto:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

O si la app ya está configurada con `.venv` dentro del proyecto:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python app.py
```

El servicio queda disponible en:

```text
http://127.0.0.1:5001/books
```

Debe responder en XML.

## 2. Actualizar datos del catálogo

Si cambias los datos del catálogo o la base de datos:

1. Actualiza la información de la base de datos o del archivo de datos del proyecto.
2. Vuelve a levantar el microservicio.
3. Refresca la aplicación Electron.

Ejemplo:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python app.py
```

## 3. Ejecutar la app Electron

Abre otra ventana de CMD:

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

La aplicación carga los libros desde el endpoint XML configurado y muestra 6 tarjetas por página.

## 4. Configuración de la IP y endpoint

Desde la app, presiona el botón `Configurar servicio` y guarda:

- host: `http://127.0.0.1:5001`
- endpoint: `/books`

La configuración queda guardada mediante `LocalStorage` en la aplicación Electron.

## 5. Recomendaciones para Windows 11

- Usa PowerShell o CMD como terminal.
- Si `python` no es reconocido, instala Python 3.11+ y vuelve a abrir la terminal.
- Si `npm` no es reconocido, instala Node.js LTS desde nodejs.org.
- Si la app no conecta con el backend, verifica que el microservicio esté corriendo y que la IP/puerto sean correctos.

## 6. Resumen de comando rápido

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate
python app.py
```

```cmd
cd "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien\apps\Electron-app"
npm install
npm start
```

> La aplicación principal se encuentra en [apps/Electron-app](apps/Electron-app).
