#!/bin/bash
set -e

cd ..
mkdir -p local-server/webroot
./build.sh
cp -r local-server/webroot prod_laggywebcams
cd prod_laggywebcams
docker-compose build --no-cache
docker-compose up -d
