# File-server
Servidor de archivos en Python
Servidor de archivos distribuido en el cual se tiene un grupos de servidores disponibles para subir archivos de cualquier tipo, 
un proxy y n clientes. Las funciones del servidor de archivso son "upload", "download" y "share". 

Funcion upload
Los clientes solicitan al proxy la informacion de los servidores disponibles para subir archivos, el proxy le responde un mensaje
con los servidores disponibles (direcciones IP) para subir archivos, el cliente procede a dividir el archivo en partes de 10MB y
los envia a cada uno de los servidores disponibles, a cada parte se le calcula una key(sha1) la cual se almacena en un archivo TXT
con el fin de tener un indice de partes almacenadas, el cliente envia informacion al proxy de donde guardo cada parte.

Funcion download

Funcion share
