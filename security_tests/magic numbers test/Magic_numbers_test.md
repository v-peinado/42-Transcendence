->Ex01. Subir un archivo con magic numbers falsos (extensión png, con magic numbers jpg)

	Ambos son tipos de imágenes  aceptadas por mi transcendente, pero pruebo que extension y magic bytes sean congruentes.

	echo -ne '\xFF\xD8\xFF' > fake.png  	# Escribe el magic number de un JPEG
	cat real.png >> fake.png             # Añade una imagen PNG real

	Explicación: Esto crea un archivo fake.png que tiene un header de JPEG pero contenido PNG.

->Ex02. Cambiar la extensión sin modificar el contenido

	mv imagen.jpg imagen.php


->Ex03. Subir un archivo Polyglot (mezcla de formatos)

	N-Los archivos polyglot contienen contenido válido para más de un tipo de archivo. Puedes probar con un PHP dentro de una imagen:

	echo '<?php echo "Hacked!"; ?>' > shell.php
	cat imagen.jpg >> shell.php
	mv shell.php imagen.jpg

	Objetivo: Ver si tu servidor ejecuta código PHP escondido dentro de un archivo aparentemente inofensivo.

->Ex04. Subir un archivo corrupto

	dd if=/dev/urandom of=corrupt.jpg bs=512 count=10

	Explicación: Esto genera un archivo aleatorio (corrupt.jpg), que probablemente no tenga un formato válido.

->Ex05. Subir un archivo con magic numbers falsos

	Lo mismo que Ex01 pero con dos archivos completamente distintos (magic numbers .txt, extension de imagen)

->imagenOK.png

	Imágen de control que funciona perfectamente.

Notas:

	Mi transcendence acepta imágenes inferiores a 2Mb.
	
	Las comprobaciones de tamaño se hacen en 3 capas (backend-django, Nginx, Modsecurity-regla customizada).


