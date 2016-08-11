#!/bin/bash

if [ $# -eq 2 ]
then
    CONTAINER=$1
    DATA=$2
    docker cp ${DATA} ${CONTAINER}:/
    docker exec ${CONTAINER} mv /`basename ${DATA}` data.csv
elif [ $# -eq 3 ]
then
    CONTAINER=$1
    DATA=$2
    TEMPLATE=$3
    docker cp ${DATA} ${CONTAINER}:/
    docker exec ${CONTAINER} mv /`basename ${DATA}` data.csv
    docker cp ${TEMPLATE} ${CONTAINER}:/
    docker exec ${CONTAINER} mv /`basename ${TEMPLATE}` template.html
else
    echo "USAGE: upload_hit.sh CONTAINER_NAME DATA_FILE [ TEMPLATE_FILE ]"
    exit 1
fi

docker exec ${CONTAINER} rm -f db.sqlite3
docker exec ${CONTAINER} python manage.py migrate
docker exec ${CONTAINER} python manage.py publish_hits template.html data.csv
docker restart ${CONTAINER}
