# Base de datos

1. Crear la base y el usuario de aplicación fuera del código versionado.
2. Ejecutar `data/library_schema.sql` con un usuario administrador.
3. Conceder los permisos mínimos indicados al final del esquema.
4. Ejecutar `database/library_seed.sql` para datos locales de demostración.
5. Configurar las credenciales en `.env`, nunca en los archivos versionados.

Ejemplo para una instalación local de PostgreSQL:

```sql
CREATE ROLE library_classifier_user LOGIN PASSWORD 'cambia-esta-clave';
CREATE DATABASE library_classifier_db OWNER library_classifier_user;
```

Después de crear la base, ejecutar los dos archivos SQL desde el usuario
administrador y configurar la misma contraseña en `.env`.
