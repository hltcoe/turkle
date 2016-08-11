#!/bin/bash

if [ $# -eq 2 ]
then
    CONTAINER=$1
    OUTPUT=$2
else
    echo "Wrong number of arguments"
    exit 1
fi
