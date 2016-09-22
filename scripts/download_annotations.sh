#!/bin/bash

if [ $# -eq 2 ]
then
    CONTAINER=$1
    OUTPUT=$2
    docker exec ${CONTAINER} python /opt/turkle/manage.py dump_results template.html results.csv
    docker cp ${CONTAINER}:/opt/turkle/results.csv ${OUTPUT}
else
    echo "USAGE: download_annotations.sh CONTAINER_NAME OUTPUT_FILE"
    exit 1
fi
