#!/usr/bin/env bash

BASEDIR=$(dirname "$0")
#echo "$BASEDIR"
cd $BASEDIR
export PMM_TEST_LEVEL="${PMM_TEST_LEVEL:-1}"
echo "Running unittest suite with PMM_TEST_LEVEL=${PMM_TEST_LEVEL}"
python3 -m unittest -vv --buffer 