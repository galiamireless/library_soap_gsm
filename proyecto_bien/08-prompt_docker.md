1. instalar docker desktop
2. ejecutar docker desktop
3. abrir terminal y ejecutar:
docker --version
docker info
docker ps
4. docker pull ollama/ollama:latest
5. docker images


1. ejecutar docker desktop
2 .crear y ejecutar ollama con almacenamiento persistente
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama/ollana:latest
3. verificar que el contender este ejecutandose 
docker ps
4. utilizando curl o su navegador vamos a verificar si ya podemos el  API REST 
curl http://localhost:11434/api/tags
5. Vamos a descargar un LLM para ejecutarlo en nuestro equipo
docker exec -it ollama ollama pull deepseek-coder
6. verificamos el modelo o modelos instalados en ollama
docker exec -it ollama ollama list
7. ejecutamos el modelo llm en nuestro contenedor de ollama
docker exec -it ollama ollama run deepseek-coder
8. Finalmente podemos probar deepseek dentro de docker desktop o en consola con curl dentro de docker desktop ejecutamos ollama run deepseek-coder en la opcion EXEC
curl https://localhost:11434/api/chat -d "{\"model\":\"deepseek-coder\", \"message\":[{\"role\":\"user\",\"content\":\"ya esta instalado mi LLM?\"}],\"stream\":false}"

curl https://localhost:11434/api/chat -d "{\"model\":\"deepseek-coder\", \"message\":[{\"role\":\"user\",\"content\":\"que es un arreglo de programacion?\"}],\"stream\":false}"

