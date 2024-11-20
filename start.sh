#!/bin/bash

# Verificar si estamos en Linux
if [ "$(uname)" == "Linux" ]; then
    # Crear directorio Docker en goinfre
    DOCKER_HOME="/goinfre/$USER/.docker"
    mkdir -p $DOCKER_HOME
    chmod 700 $DOCKER_HOME

    # Configurar Docker rootless
    dockerd-rootless-setuptool.sh install
    
    # Exportar la variable DOCKER_HOST
    export DOCKER_HOST="unix://$DOCKER_HOME/run/docker.sock"
    
    # Asegurar que los directorios de volúmenes existan con permisos correctos
    mkdir -p /goinfre/$USER/docker-volumes
    chmod 700 /goinfre/$USER/docker-volumes
fi

# Ejecutar make
make up