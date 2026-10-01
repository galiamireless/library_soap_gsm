# Ejercicio: Comparacion PostgreSQL y Redis

## Objetivo

Medir desde CMD de Windows una lectura puntual de un libro en PostgreSQL y el `GET` en Redis de un JSON equivalente. PostgreSQL esta configurado en `.env`; Redis corre en Ubuntu sobre WSL2 y se alcanza desde Windows por `localhost:6379`.

La prueba mantiene ambas conexiones abiertas, calienta las operaciones antes de medir, alterna el orden entre PostgreSQL y Redis y verifica que ambos devuelvan exactamente el mismo valor. No crea tablas ni modifica registros permanentes en PostgreSQL. Solo crea y elimina una clave Redis temporal con nombre unico.

## Preparacion

Abre CMD y entra a la raiz del proyecto:

```cmd
cd /d "C:\Users\galia\OneDrive\Escritorio\7mo semestre\Integracion\pagina web\SOAP\library_soap_gsm\proyecto_bien"
.venv\Scripts\activate.bat
```

Inicia Redis en WSL y comprueba la conexion:

```cmd
wsl -d Ubuntu -- sudo service redis-server start
wsl -d Ubuntu -- redis-cli ping
```

La respuesta debe ser `PONG`. Instala el cliente Redis para Python en el entorno virtual:

```cmd
python -m pip install redis
```

El entorno ya debe tener `psycopg` y `python-dotenv` porque forman parte de las dependencias del servicio. El script lee los parametros PostgreSQL de `.env` y usa `REDIS_URL=redis://localhost:6379/0` por defecto. No imprime secretos.

## Script entregable

Guarda este bloque como `benchmark_redis.py` en la raiz `proyecto_bien`, junto a `.env` y `requirements.txt`:

```python
import argparse
import math
import os
import platform
import statistics
import time
import uuid
from pathlib import Path

import psycopg
import redis
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percent * len(ordered)) - 1)
    return ordered[index]


def measure_postgres(cursor, isbn: str, expected_json: str) -> float:
    start = time.perf_counter_ns()
    cursor.execute(
        "SELECT to_jsonb(b)::text FROM library.books AS b WHERE b.isbn = %s",
        (isbn,),
    )
    row = cursor.fetchone()
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    if row is None or row[0] != expected_json:
        raise RuntimeError("PostgreSQL devolvio un registro distinto durante la prueba.")
    return elapsed_ms


def measure_redis(client, key: str, expected_json: str) -> float:
    start = time.perf_counter_ns()
    value = client.get(key)
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
    if value != expected_json:
        raise RuntimeError("Redis devolvio un valor distinto o la clave expiro.")
    return elapsed_ms


def report(name: str, values: list[float]) -> dict[str, float]:
    result = {
        "min": min(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p95": percentile(values, 0.95),
        "max": max(values),
        "ops_per_second": 1000 / statistics.fmean(values),
    }
    print(
        f"{name:<12} "
        f"min={result['min']:.4f} ms  "
        f"media={result['mean']:.4f} ms  "
        f"mediana={result['median']:.4f} ms  "
        f"p95={result['p95']:.4f} ms  "
        f"max={result['max']:.4f} ms  "
        f"ops/s~={result['ops_per_second']:.1f}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compara una lectura puntual de PostgreSQL y Redis."
    )
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=50)
    args = parser.parse_args()
    if args.iterations < 20 or args.warmup < 0:
        parser.error("Usa al menos 20 iteraciones y un calentamiento igual o mayor que cero.")

    pg_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "library_classifier_db"),
        "user": os.getenv("DB_USER", "library_classifier_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
        "application_name": "redis-vs-postgresql-benchmark",
    }
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    key = f"benchmark:books:{uuid.uuid4()}"
    key_created = False
    pg_connection = None

    try:
        pg_connection = psycopg.connect(**pg_config)
        redis_client.ping()
        with pg_connection.cursor() as cursor:
            cursor.execute(
                "SELECT isbn, to_jsonb(b)::text "
                "FROM library.books AS b ORDER BY b.isbn LIMIT 1"
            )
            sample = cursor.fetchone()
            if sample is None:
                raise RuntimeError(
                    "library.books esta vacia. Carga datos de prueba antes de medir."
                )
            isbn, payload = sample

            redis_client.set(key, payload, ex=3600)
            key_created = True
            if redis_client.get(key) != payload:
                raise RuntimeError("No se pudo verificar el valor de prueba en Redis.")

            postgres_times = []
            redis_times = []
            for _ in range(args.warmup):
                measure_postgres(cursor, isbn, payload)
                measure_redis(redis_client, key, payload)

            for iteration in range(args.iterations):
                if iteration % 2 == 0:
                    postgres_times.append(measure_postgres(cursor, isbn, payload))
                    redis_times.append(measure_redis(redis_client, key, payload))
                else:
                    redis_times.append(measure_redis(redis_client, key, payload))
                    postgres_times.append(measure_postgres(cursor, isbn, payload))

            cursor.execute("SHOW server_version")
            postgres_version = cursor.fetchone()[0]

        redis_version = redis_client.info("server")["redis_version"]
        pg_stats = report("PostgreSQL", postgres_times)
        redis_stats = report("Redis", redis_times)
        speedup = pg_stats["median"] / redis_stats["median"]

        print(f"\nPython: {platform.python_version()} ({platform.system()})")
        print(f"PostgreSQL: {postgres_version}")
        print(f"Redis: {redis_version}")
        print(f"Registro: ISBN {isbn}; payload {len(payload.encode('utf-8'))} bytes")
        print(f"Iteraciones medidas: {args.iterations}; calentamiento: {args.warmup}")
        print(f"Relacion de medianas PostgreSQL/Redis: {speedup:.2f}x")
        print("Las operaciones/s son estimaciones secuenciales a partir de la media.")
    finally:
        if key_created:
            redis_client.delete(key)
        redis_client.close()
        if pg_connection is not None:
            pg_connection.close()


if __name__ == "__main__":
    main()
```

## Ejecucion

Con Redis activo, `.venv` activado y CMD situado en `proyecto_bien`, ejecuta:

```cmd
python benchmark_redis.py --iterations 1000 --warmup 50
```

Para una repeticion mas larga:

```cmd
python benchmark_redis.py --iterations 5000 --warmup 200
```

Si el script indica que `library.books` esta vacia, carga el conjunto de demostracion mediante `proyecto_bien/database/library_seed.sql` en pgAdmin. Si falla la conexion, revisa las variables DB de `.env`, inicia PostgreSQL y confirma `PONG` para Redis. La clave temporal de Redis tiene vencimiento de una hora y se elimina al terminar normalmente.

## Reporte de resultados

**Fecha de ejecucion:** 2026-10-01  
**Cliente del benchmark:** Python ejecutado desde CMD en Windows  
**PostgreSQL:** servicio local, esquema `library`, tabla `library.books`  
**Redis:** Ubuntu en WSL2, accesible desde Windows por `localhost:6379`  
**Carga:** 1,000 lecturas medidas por tecnologia, 50 lecturas de calentamiento, una conexion persistente por tecnologia.

### Resultados

| Tecnologia | Operacion | Minimo (ms) | Media (ms) | Mediana (ms) | p95 (ms) | Maximo (ms) | Ops/s aproximadas |
|---|---|---:|---:|---:|---:|---:|---:|
| PostgreSQL | SELECT por ISBN y serializacion JSON | 0.1813 | 0.6103 | 0.5642 | 1.0517 | 2.7012 | 1,638.4 |
| Redis | GET del mismo JSON | 0.5733 | 1.4647 | 1.3781 | 2.4352 | 4.1735 | 682.7 |

**Versiones:** Python 3.14.0 en Windows, PostgreSQL 14.24 y Redis 8.0.5 en Ubuntu/WSL2.  
**Registro:** ISBN `9786070001001`; payload JSON de 393 bytes.  
**Relacion de medianas PostgreSQL/Redis:** `0.41x` (PostgreSQL tuvo la menor mediana en esta ejecucion).

Los tiempos cambian con carga del equipo, versiones, energia, virtualizacion, red y estado del servicio. Estos valores corresponden a esta ejecucion concreta y no deben presentarse como cifras universales.

### Comparacion cualitativa

| Aspecto | PostgreSQL | Redis |
|---|---|---|
| Tipo de operacion medida | Consulta SQL parametrizada por clave primaria y conversion a JSON | Lectura `GET` por clave |
| Persistencia y funcion | Base relacional persistente; fuente de verdad del catalogo | Almacen en memoria para datos temporales/cache; no reemplaza el catalogo relacional |
| Costo incluido en esta prueba | Viaje local al servidor, ejecucion SQL, lectura de fila y serializacion JSON | Viaje local hacia WSL2 y lectura del valor ya serializado |
| Concurrencia | El script mide un cliente secuencial, no carga concurrente | El script mide un cliente secuencial, no carga concurrente |
| Consistencia | La fila leida es el dato persistente | El valor puede quedar desactualizado si no se invalida o expira la cache |
| Uso indicado | Escrituras, relaciones, consultas flexibles e integridad transaccional | Cache de lecturas repetidas, contadores con TTL y estado temporal compartido |

### Interpretacion y limites

La prueba compara una lectura puntual y serializada, no todas las capacidades de las dos tecnologias. Las dos conexiones se reutilizan, se verifica que el contenido sea identico y se alterna cual tecnologia se mide primero. La mediana reduce el efecto de pausas ocasionales; p95 muestra una parte de las lecturas lentas. La razon de medianas se interpreta asi: un valor mayor que `1x` significa que Redis tuvo menor mediana en esta ejecucion; menor que `1x` significa que PostgreSQL la tuvo.

En esta corrida, la mediana de Redis fue aproximadamente `2.44x` la de PostgreSQL (`1.3781 / 0.5642`). La media estimada fue `2.40x` mayor para Redis, y PostgreSQL alcanzo alrededor de `2.40x` las operaciones por segundo estimadas. Redis no fue mas rapido en este montaje: su servidor corre dentro de WSL2 y cada `GET` medido cruza la frontera entre Windows y Linux, mientras PostgreSQL es local a Windows. Ese costo de comunicacion ayuda a explicar el resultado y no representa una comparacion de Redis nativo contra PostgreSQL bajo condiciones identicas.

Las operaciones por segundo son `1000 / media en milisegundos`, calculadas a partir de las latencias individuales. No representan throughput bajo concurrencia porque el script usa un solo cliente secuencial. El p95 y maximo de Redis tambien fueron superiores en esta corrida; las pausas ocasionales pueden depender de la virtualizacion, la planificacion del sistema y la carga de ambas instancias.

### Conclusion

Redis puede ser conveniente para acelerar lecturas repetidas de datos que toleran cache, compartir estado temporal entre instancias o implementar contadores con expiracion. Esta prueba no demostro una mejora de latencia al conectar desde Windows a Redis en WSL2; para medir el uso previsto en despliegue convendria repetirla con el microservicio y Redis en el mismo entorno de red y, despues, con concurrencia controlada. PostgreSQL debe seguir siendo la fuente persistente y autoritativa para libros y demas datos relacionados. No se debe elegir Redis solo por una prueba de microsegundos: tambien se debe considerar invalidacion, consistencia, disponibilidad y operacion adicional.

