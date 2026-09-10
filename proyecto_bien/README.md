# Proyecto Bien · Library Classifier

Reorganización independiente del servicio de clasificación de conceptos Cloud.
Conserva las operaciones SOAP y las rutas de consulta de libros, pero usa una
estructura modular inspirada en el repositorio de referencia:

```text
proyecto_bien/
├── apps/services/soap/   # aplicación Flask, contrato y pruebas del servicio
├── data/                  # esquema y decisiones del modelo
├── database/              # datos iniciales y operación de base de datos
└── docs/                  # prompts, arquitectura y plan de pruebas
```

## Inicio rápido

```bash
cd proyecto_bien
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Crear la base y cargar el catálogo de ejemplo:

```bash
psql -U postgres -c "CREATE DATABASE library_classifier_db"
psql -U postgres -d library_classifier_db -f data/library_schema.sql
psql -U postgres -d library_classifier_db -f database/library_seed.sql
```

Ejecutar el servicio:

```bash
.venv/bin/python -m apps.services.soap.app
```

El puerto por defecto es `5001`, configurable mediante `.env`. Las respuestas
son XML por defecto; `?format=json` conserva una representación JSON útil para
clientes que no consumen SOAP.

## Rutas principales

- `GET /books`
- `GET /books/<isbn>`
- `GET /books/minimal`
- `GET /books/concepts`
- `GET /cloud-concepts` (alias compatible)
- `GET /health`
- `GET /library-classifier.wsdl`
- `POST /soap`

Las rutas de catálogo leen el esquema propio `library`; el servicio no depende
de tablas internas de otro proyecto.

## Pruebas

```bash
.venv/bin/pytest -q apps/services/soap/tests
```
