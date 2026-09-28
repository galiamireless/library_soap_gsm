Ejercicio Guiado: planteamiento
trabajando en la carpeta library_soap_gsm/proyecto_bien. Retomamos los microservicios de la libreria en linea: login (register/login/logout/session/health) y book (catalogo de libros, con el esquema de bases de datos que tenemos en postgres)

- Objetivo: proteger las operaciones de escritura del servicio book (POST, PUT, PATCH, DELETE) exigiendo un JWT valido emitido por el servicio login
- Se mantiene publico: GET /api/books y GET /api/books/{isbn} no requieren token; cualquiera puede consultar el catalogo
- Se protege: crear, actualizar o eliminar libros si requiere authorization: Bearer <token>.

En /login, tras validar el password_hash

PROTEGER TODO, INCLUSO ENDPOINTS DE LOGIN. tiene que validar toodos los tokens siempre, y NO USAR alg NONE
emision del token (servicio login)

LOS MICROSERVICIOS DEBEN ESTAR PROTEGIDOS CON JWT. en login tenemos sesiones, cookies, es basicamente implementar el jwt en la aplicacion. GET books debe ser publico.

Se necesitara tomar evidencias con la aplicacion corriendo atras y las evidencias de lo pedido en este prompt encima de la app corriendo, por favor dame un readme_planteamiento.md con todo desde 0 como si mi terminal CMD estuviera en blanco, desde entrar en el cd, env, correr python, la base de datos NO PSQL YA QUE NO PUEDO USAR PSQL, QUE HACER PARA CADA EVIDENCIA, ETC. TODO DOCUMENTADO.

CUIDA TODAS LAS APLICACIONES ES DECIR LA MONOLITO, SOAP, ELECTRON, LOGIN, JWT ETC. QUE NADA SE ROMPA.