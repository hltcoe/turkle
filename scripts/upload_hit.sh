#!/bin/bash

if [ $# -eq 2 ]
then
    CONTAINER=$1
    DATA=$2
elif [ $# -eq 3 ]
then
    CONTAINER=$1
    TEMPLATE=$2
    DATA=$3
else
    echo "Wrong number of arguments"
    exit 1
fi
