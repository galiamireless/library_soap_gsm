# Reflexion

Separar la autenticacion en un microservicio permite que el catalogo y sus clientes sigan funcionando aunque cambien las reglas de usuarios. La cuenta vive en `library.users`, dentro de la misma base de datos del proyecto, pero no se mezcla con `clasificadores`: son responsabilidades distintas y cada una puede evolucionar sin romper a la otra.

Guardar solo `password_hash` es esencial. Una contrasena en texto plano convierte una fuga de base de datos en un compromiso inmediato de todas las cuentas. El hash se calcula con un algoritmo lento y resistente a ataques de diccionario; el servicio nunca devuelve ese valor ni lo incluye en una sesion.

La verificacion por correo evita activar cuentas con direcciones que el usuario no controla. El mensaje sale por la instancia local de Postfix, usando `info@localhost` como remitente configurado, y el token tiene una expiracion. En una instalacion real, Postfix debe tener un dominio propio y entregar directamente o mediante un relay administrado por la institucion; no se depende de SMTP de Google u Outlook.

Las sesiones combinan la cookie firmada de Flask con un token aleatorio almacenado en `library.auth_sessions`. La cookie identifica la sesion, pero la autorizacion se consulta en PostgreSQL y puede revocarse con `/logout`. Las respuestas ofrecen XML por defecto, JSON cuando se solicita y enlaces HATEOAS para que un cliente pueda continuar el flujo sin conocer rutas adicionales por adelantado.
