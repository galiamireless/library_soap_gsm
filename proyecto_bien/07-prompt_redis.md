Desarrolla los siguientes microservicios:
1. Users: microservicio que administre usuarios, roles, correos y contraseñas.
2. Authors: microservicio que administra autores y sus relaciones con libros.
3. Pedidos: microservicio que crea y gestiona pedidos, líneas de pedido, stock y estados.
4. Pagos: microservicio que registra pagos y actualiza el estado de los pedidos.
(serian en total 6 microservicion con estos 4 y los 2 que ya se tenian)

INCORPORA REDIS A LA APLICACION DONDE SEA PERTINENTE.

CUIDA QUE TODO FUNCIONE Y QUE LO QUE YA SE TENIA ANTERIORMENTE SI BIEN ESTAMOS AGREGANDO NUEVAS COSAS, TODO FUNCIONE A LA PERFECCION LOS 6 MICROSERVICIOS, LOS NUEVOS Y LOS DE ANTES, LOGIN Y BOOKS ASI COMO ELECTRON Y SOAP.

DESPUES DE HACER DESARROLLAR LO SOLICITADOS HAZ UN readmeMicroservicios.md DONDE INDIQUES EL PASO A PASO PARA CORRER TODO DESDE CMD SIN PSQL (NO PUEDO USARLO EN MI COMPU) Y AL FINAL AGREGA UNA SECCION DE EVIDENCIAS DONDE ME INDIQUES QUE ES LO QUE SERA CADA EVIDENCIA, EL SCRIPT PARA CORRERLO O HACERLO Y LO ESPERADO. HAZ DE 5 A 10 EVIDENCIAS. BASICAMENTE ESTE ARCHIVO DEBE DE DECIRME COMO HACER Y CORRER TODO SIN TENER QUE CONSULTAR NADA MAS.

Verifica que login valide credenciales y emite un JWT firmado con SECRET_KEY, algoritmo
HS256 y expiración de 20 minutos. Debe renovarse antes de caducar.
• Users, Authors, Pedidos y Pagos: todas las operaciones POST, PUT, PATCH y DELETE deben exigir: Authorization: Bearer <JWT>
• Lecturas GET: pueden mantenerse públicas si solo consultan información; las lecturas administrativas deberían exigir JWT y permisos.
Validación: cada servicio debe verificar firma, algoritmo, expiración y claims del token antes de modificar datos.
• Secretos: todos los servicios deben compartir JWT_SECRET_KEY, configurada mediante variables de entorno, nunca escrita directamente en el código.
• Roles: el JWT debe incluir user_id y role_id; las operaciones administrativas deben comprobar que el usuario tenga rol autorizado.
• CORS: permitir únicamente los orígenes de las aplicaciones cliente en producción.
• Seguridad adicional: usar HTTPS, no guardar contraseñas ni tokens en logs y devolver 401 para tokens ausentes o inválidos y 403 para roles insuficientes.