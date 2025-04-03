#!/bin/bash

# Remove volumes and stop related containers
docker stop buildx_buildkit_dockerbuilder0
docker rm buildx_buildkit_dockerbuilder0 web-app-sgwebimage-1 web-app-postgres-1
docker volume rm web-app_smartgate-data
