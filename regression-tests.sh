#!/bin/bash

C=2
GREP='.'
if [ $# -eq 1 ]
then
    C=$1
    GREP='WORKS'
fi

if [ "$#" -lt 2 ]; then echo "Error in parameters. Usage: regression-tests.sh SRCLANG TRGLANG"; exit 1; fi

bash wiki-tests.sh Regression $1 $2 update | grep -C $C "$GREP"



