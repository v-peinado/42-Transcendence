# Guía de Comandos para Manejo de Ramas en Git

## Listar Ramas

- **Ver ramas locales**:
	```bash
	git branch

- **Ver todas las ramas (locales y remotas):**
	```bash
	git branch -a
	

## Crear ramas

- **Crear una nueva rama y cambiar a ella:**
	```bash
	git checkout -b nombre-de-la-rama

- **Cambiar a una rama existente:**
	```bash
	git checkout nombre-de-la-rama

- **Crear una nueva rama basada en una rama remota y cambiar a ella:**
	```bash
	git checkout -b nombre-de-la-rama origin/nombre-de-la-rama

## Renombrar Ramas

- **Renombrar la rama actual:**
	```bash
	git branch -m nuevo-nombre

- **Renombrar una rama específica:**
	```bash
	git branch -m nombre-antiguo nuevo-nombre

## Borrar Ramas

- **Borrar una rama local:**
	```bash
	git branch -d nombre-de-la-rama

-   **Usa -D para forzar el borrado si la rama tiene cambios no fusionados.**

- **Borrar una rama remota:**
	```bash
	git push origin --delete nombre-de-la-rama

## Fusionar Ramas

- **Fusionar una rama en la actual:**
	```bash
	git merge nombre-de-la-rama

- **Fusionar una rama remota en la actual:**
	```bash
	git pull origin nombre-de-la-rama

## Ver Cambios y Estados de Ramas

- **Ver la rama actual y en qué commit está cada rama:**
	```bash
	git branch -v

- **Ver el historial de cambios en todas las ramas:**
	```bash
	git log --oneline --all --graph --decorate

## Sincronización de Ramas con el Remoto

- **Actualizar el repositorio local con ramas remotas:**
	```bash
	git fetch

- **Actualizar y fusionar todos los cambios de una rama remota en la rama actual:**
	```bash
	git pull origin nombre-de-la-rama

- **Enviar cambios de la rama actual al repositorio remoto:**
	```bash
	git push origin nombre-de-la-rama

## Otros Comandos Útiles

- **Ver diferencias entre la rama actual y otra rama:**
	```bash
	git diff nombre-de-la-rama

- **Ver el último commit de cada rama:**
	```bash
	git show-branch

- **Listar todas las ramas que han sido fusionadas en la rama actual:**
	```bash
	git branch --merged

- **Listar todas las ramas que no han sido fusionadas en la rama actual:**
	```bash
	git branch --no-merged
