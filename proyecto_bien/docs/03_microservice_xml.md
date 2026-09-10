# Prompt de microservicio XML

Construir un microservicio Flask que consulte el catálogo normalizado del
esquema `library`. Debe mostrar todos los libros, un libro por ISBN, un resumen
mínimo, conceptos Cloud y health. XML es la respuesta predeterminada; JSON se
activa con `format=json`. El servicio debe usar SQL parametrizado, pool de
conexiones, límites de body y respuestas de error consistentes.
