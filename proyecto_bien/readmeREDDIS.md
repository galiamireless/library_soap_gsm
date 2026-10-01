# Descargar e instalar Redis en Windows con WSL2

Esta guia instala Redis en Ubuntu dentro de WSL2. Podras iniciar y probar Redis desde CMD y conectarte a el desde aplicaciones de Windows usando `localhost:6379`.

## Requisitos

- Windows 10 actualizado o Windows 11.
- Conexion a Internet durante la instalacion.
- Acceso de administrador para instalar WSL si aun no esta instalado.

## 1. Instalar WSL2 y Ubuntu desde CMD

1. Abre el menu Inicio, escribe `cmd`.
2. Haz clic derecho en **Simbolo del sistema** y selecciona **Ejecutar como administrador**.
3. Instala WSL con la distribucion Ubuntu:

```cmd
wsl --install -d Ubuntu
```

4. Si Windows solicita reiniciar, reinicia la computadora.
5. Despues del reinicio, abre **Ubuntu** desde el menu Inicio.
6. La primera vez, Ubuntu pedira crear un nombre de usuario y una contrasena de Linux. No tienen que ser iguales a los de Windows. Al escribir la contrasena no veras caracteres en pantalla; escribe y presiona Enter.

Si WSL ya estaba instalado, puedes comprobar las distribuciones desde CMD:

```cmd
wsl --list --verbose
```

Identifica el nombre exacto de Ubuntu. Los comandos de esta guia usan `Ubuntu`; si tu distribucion aparece con otro nombre, reemplaza `Ubuntu` por ese nombre.

## 2. Descargar e instalar Redis en Ubuntu

Abre la aplicacion **Ubuntu** desde Inicio. Ejecuta cada comando y espera a que termine antes de ingresar el siguiente:

```bash
sudo apt update
sudo apt install -y redis-server
```

El primer comando actualiza la lista de paquetes y el segundo descarga e instala Redis. Si Ubuntu pregunta por la contrasena, escribe la contrasena de Linux creada en el paso anterior.

## 3. Iniciar Redis y verificar la instalacion

En la terminal de Ubuntu inicia el servicio y comprueba su estado:

```bash
sudo service redis-server start
sudo service redis-server status
```

Ahora envia una prueba al servidor Redis:

```bash
redis-cli ping
```

La respuesta correcta es:

```text
PONG
```

Tambien puedes probar que Redis guarde y devuelva un valor:

```bash
redis-cli SET prueba "Redis funciona"
redis-cli GET prueba
```

El segundo comando debe mostrar `Redis funciona`.

## 4. Iniciar y comprobar Redis desde CMD

Redis corre dentro de Ubuntu/WSL, pero puedes administrarlo desde una ventana normal de CMD. Abre CMD y ejecuta:

```cmd
wsl -d Ubuntu -- sudo service redis-server start
wsl -d Ubuntu -- redis-cli ping
```

La segunda linea debe responder `PONG`. Si el nombre de tu distribucion no es `Ubuntu`, usa el nombre que viste con `wsl --list --verbose`.

Para apagar Redis desde CMD:

```cmd
wsl -d Ubuntu -- sudo service redis-server stop
```

## 5. Conectarse desde una aplicacion de Windows

Cuando Redis este iniciado, configura tu aplicacion para conectarse a:

```text
Host: localhost
Puerto: 6379
```

Para probar el servidor desde CMD puedes ejecutar el cliente de Redis dentro de WSL:

```cmd
wsl -d Ubuntu -- redis-cli -h 127.0.0.1 -p 6379 ping
```

Debe responder `PONG`. No necesitas instalar `redis-cli` como programa de Windows para que una aplicacion de Windows se conecte a Redis en WSL2.

## 6. Uso posterior

Cada vez que reinicies Windows o necesites volver a usar Redis, inicia el servicio desde CMD:

```cmd
wsl -d Ubuntu -- sudo service redis-server start
```

Comprueba que quedo activo:

```cmd
wsl -d Ubuntu -- redis-cli ping
```

Al terminar, puedes detenerlo con:

```cmd
wsl -d Ubuntu -- sudo service redis-server stop
```

Para esta instalacion local no abras el puerto `6379` en el firewall ni cambies la configuracion de Redis para aceptar conexiones de otras computadoras.









## Incorporar Redis en los microservicios

Redis es un servicio compartido al que se conectan los microservicios que lo necesitan. No se instala una instancia independiente dentro de cada microservicio: en desarrollo, los servicios de Windows pueden conectarse al Redis de WSL usando `localhost:6379`. Si los servicios corren en otra maquina, contenedor o VM, `localhost` apunta a esa maquina o contenedor, no a tu PC; en ese caso configura la IP privada o el nombre de servicio de Redis.

### Configuracion de cada servicio

1. Inicia Redis en WSL y confirma que `redis-cli ping` responda `PONG`.
2. En el entorno virtual de cada microservicio Python que vaya a usar Redis, instala el cliente:

```cmd
pip install redis
```

3. Agrega `redis` a `requirements.txt` del proyecto para que la dependencia quede registrada y pueda instalarse en otros equipos.
4. Configura la direccion como variable de entorno `REDIS_URL`. Para desarrollo local:

```text
REDIS_URL=redis://localhost:6379/0
```

5. Crea un cliente Redis reutilizable al iniciar el servicio, leyendo la URL del entorno. Ejemplo con el paquete `redis` para Python:

```python
import os
import redis

redis_client = redis.Redis.from_url(
	os.getenv("REDIS_URL", "redis://localhost:6379/0"),
	decode_responses=True,
)
```

El cliente se crea una vez por proceso y se comparte entre las operaciones del microservicio. Evita abrir una conexion nueva por cada solicitud.

### Usos recomendados en este proyecto

- **Login:** guardar temporalmente el identificador `jti` de un JWT revocado hasta que expire. Al validar un token, el servicio consulta si su `jti` esta en Redis; asi se puede invalidar una sesion antes de que venza el JWT. Guarda solo el identificador, nunca la contrasena ni el JWT completo. Tambien se pueden limitar intentos de inicio de sesion con contadores que expiren automaticamente.
- **SOAP / catalogo:** guardar durante un tiempo corto resultados de consultas repetidas, como el listado de libros o conceptos. Antes de consultar PostgreSQL, el servicio revisa la clave de cache; si no existe, consulta PostgreSQL y guarda el resultado con un TTL. Despues de crear o actualizar datos, invalida las claves relacionadas para reducir respuestas desactualizadas.
- **Estado compartido entre instancias:** si se ejecutan varias copias del mismo microservicio, Redis permite compartir contadores, limites y datos temporales. La memoria local de una instancia no se comparte con las demas.

Ejemplo esquematico de cache para una consulta de libros:

```python
import json

cache_key = "catalog:books"
cached_books = redis_client.get(cache_key)

if cached_books is not None:
	books = json.loads(cached_books)
else:
	books = repository.list_books()
	redis_client.set(cache_key, json.dumps(books), ex=60)
```

El parametro `ex=60` hace que la entrada caduque en 60 segundos. Cuando una operacion modifica libros, elimina la clave con `redis_client.delete("catalog:books")` para que la proxima consulta lea datos actualizados de PostgreSQL.

### Por que conviene y cuando usarlo

Redis mantiene los datos en memoria y ofrece lecturas muy rapidas, expiracion automatica con TTL y operaciones atomicas utiles para contadores. Esto puede reducir consultas repetidas a PostgreSQL, compartir estado entre instancias y hacer mas sencilla la revocacion temprana de JWT o la limitacion de intentos.

Redis no es obligatorio para todo microservicio ni debe agregarse sin un caso de uso. Conviene incorporarlo cuando hay consultas repetidas, estado temporal que debe compartirse entre instancias, necesidad de expirar datos automaticamente o carga que justifique descargar trabajo de PostgreSQL. Si la aplicacion es pequeña y no presenta esas necesidades, PostgreSQL y el flujo actual pueden ser suficientes.

Mantén PostgreSQL como fuente permanente y confiable de libros, usuarios y clasificaciones. La cache de Redis debe poder reconstruirse; si Redis no esta disponible, define el comportamiento esperado (por ejemplo, omitir la cache y consultar PostgreSQL cuando sea seguro). Para datos sensibles o decisiones de autenticacion, no permitas que una falla de Redis se interprete como una autorizacion valida. En despliegues reales protege Redis con red privada, autenticacion y reglas de firewall; no expongas el puerto `6379` a Internet.