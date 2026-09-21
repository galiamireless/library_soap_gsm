DENTRO DE library_soap_gsm/proyecto_bien trabajaremos ahi.
Objetivo: Desarrollar un microservicio independiente de autenticación y gestión básica de usuarios para la plataforma de librería en línea existente. El servicio deberá desarrollarse con Python, Flask, Psycopg 3 y PostgreSQL, utilizar la base de datos actual del proyecto y exponer sus respuestas tanto en XML como en JSON. Esto debe estar en library_soap_gsm/proyecto_bien/apps. solo es un microservicio por lo que NO hay interfaces.

El propósito del ejercicio es practicar integración entre aplicaciones, diseño de API, persistencia en PostgreSQL, normalización, autenticación, sesiones, protección de contraseñas y representación de un mismo recurso en diferentes formatos.

Requerimientos funcionales: El microservicio deberá implementar las siguientes operaciones:
Método
Endpoint
Función
POST
/register
Registrar un nuevo usuario
POST
/login
Autenticar al usuario e iniciar sesión
POST
/logout
Cerrar la sesión
GET
/session
Consultar si existe una sesión autenticada
GET
/health
Verificar el estado del microservicio y PostgreSQL

Todos los endpoints deberán soportar:  ?format=xml  y ?format=json, si no se especifica el parámetro format, XML será el formato predeterminado., por ejemplo: POST /login     POST /login?format=xml deberán responder XML, mientras que:  POST /login?format=json deberá responder JSON. El registro deberá solicitar:
nombre
apellido paterno
apellido materno
email
password

El correo deberá validarse antes de registrarse y deberá ser único. La contraseña nunca deberá almacenarse en texto plano. El sistema almacenará únicamente un hash seguro de la contraseña. Debe usarse Postfix.

La autenticación deberá verificar las credenciales contra PostgreSQL y, cuando sean correctas, crear una sesión del lado de Flask que permita identificar al usuario en solicitudes posteriores.

El correo deberá validarse antes de registrarse y deberá ser único. La contraseña nunca deberá almacenarse en texto plano. El sistema almacenará únicamente un hash seguro de la contraseña.

La autenticación deberá verificar las credenciales contra PostgreSQL y, cuando sean correctas, crear una sesión del lado de Flask que permita identificar al usuario en solicitudes posteriores.

Crea el microservicio en el directorio apps/services/login
Modifica e integra las tablas necesarias a la base de datos library
Despliega el microservicio en el puerto 5000
Utiliza Swagger para documentar los endpoints en XML y JSON
Valida que todos los endpoint funcionen correctamente (anexa evidencia screenshots) -> AGREGA UN README LLAMADO EVIDENCIAS.MD QUE INDIQUE QUE HACER EXACTAMENTE PARA OBTENER LAS EVIDENCIAS DESDE CMD DESDE EL PATH, ACTIVAR TODO, PRENDER E INSTALAR LO NECESARIO PARA QUE CORRA Y TODOS LOS COMANDOS PARA PROBAR CADA ENDPOINT, ASI COMO MONOREPO, ELECTRONAPP Y LOGIN, viendo que devuelve el json.
AGREGA DENTRO DE proyecto_Bien o donde este el login agrega un archivo reflexion.md donde haya una reflexión personal del porque se tiene que hacer así.

Recuerda, no necesitamos almacenar la contraseña dos veces ni crear una tabla exclusivamente para passwords. password_hash pertenece naturalmente a la cuenta de usuario.
necesitamos crear un post, debes reestructurar la base de datos y esto puede corromper el monolito, el Electron-app etc porl lo que hay que tomar en cuenta esto. No toques la funcionalidad del monolito ni electron-app, Hay que agregar una validacion mediante correo electronico con HATETOA.
No usar smtp de google ni outlook, la cuenta debe salir de mi instancia, es decir si necesitar haber un servidor de correo electronico se debe de hacer, no se debe salir. El servidor deber tener el correo por ejemplo info@localhost y debe llegar de verdad a un correo real.

Otro detalle pasado: /books tambien debe tener post no solo get.