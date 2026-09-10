# Métricas de operación

Registrar durante la verificación local:

- tiempo de respuesta de `/health` con PostgreSQL arriba y apagado;
- tiempo de espera del pool bajo concurrencia;
- tamaño de request/response SOAP;
- cantidad de libros devueltos por cada consulta;
- porcentaje de respuestas con XML frente a JSON.

Los valores deben medirse en el entorno de ejecución y no fijarse como datos
inventados en esta documentación.
