# Reflexion personal

## Lo que hice

En esta actividad construí una aplicacion de escritorio con Electron para consultar y mostrar el catalogo de libros que entrega el microservicio de biblioteca. La aplicacion consume la respuesta XML del endpoint `/books`, interpreta los datos de cada libro y los presenta en tarjetas con informacion como titulo, autor, ISBN, editorial, formato, precio y stock.

Tambien agregue paginacion y una ventana de configuracion para cambiar el host y el endpoint del servicio. La configuracion se guarda en `LocalStorage`, por lo que no es necesario escribir nuevamente la direccion cada vez que se abre la aplicacion.

Una parte importante fue resolver el problema de las imagenes. Las URLs originales eran de ejemplo y no apuntaban a imagenes reales. Por eso asigne una URL diferente para cada ISBN conocido, procurando que la imagen tuviera relacion con el contenido del libro. Para el libro de sistemas distribuidos use una imagen relacionada con redes y servidores, mientras que para el libro de XML use otra imagen relacionada con tecnologia y computadoras.

## Por que se tiene que hacer asi

La aplicacion debe consumir el microservicio y no duplicar los libros directamente en Electron porque el backend es la fuente central de datos. De esta forma, si cambian el stock, el precio o la descripcion, la aplicacion puede mostrar la informacion actualizada al volver a consultar el endpoint.

Se utiliza XML porque es el formato que define el servicio y porque permite mantener la interoperabilidad con otros sistemas. Electron recibe ese XML, lo procesa con `DOMParser` y transforma cada elemento `book` en un objeto que la interfaz puede mostrar.

La configuracion del servicio se separa de la interfaz para poder cambiar la direccion del backend sin modificar el codigo fuente. Esto es necesario cuando el servicio se ejecuta en otra computadora, en otra IP o en un puerto diferente.

Las imagenes se seleccionan por ISBN porque el ISBN identifica de forma unica a cada libro. Usar ese dato evita depender solamente del titulo y permite que cada registro tenga una imagen especifica. Ademas, se conserva una imagen de respaldo para evitar que una URL rota deje una tarjeta vacia.

## Aprendizaje personal

Aprendi que una aplicacion puede parecer terminada visualmente y aun asi depender de varios elementos externos para funcionar correctamente: el backend debe estar encendido, la base de datos debe responder y las URLs externas deben ser validas. Tambien comprendi que los errores de conexion y los errores de contenido son problemas diferentes. La conexion con el servicio puede funcionar correctamente aunque una imagen no cargue.

La solucion final me ayudo a entender mejor la responsabilidad de cada parte del sistema: el backend entrega los datos, Electron los consume y presenta, y la interfaz debe manejar los casos en los que un dato externo no esta disponible. Por eso considero importante agregar validaciones y respaldos, ya que hacen que la aplicacion sea mas resistente y util para el usuario.
