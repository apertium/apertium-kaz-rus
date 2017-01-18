#!/bin/bash

C=2
GREP='.'
if [ $# -eq 1 ]
then
    C=$1
    GREP='WORKS'
fi

bash wiki-tests.sh Regression rus kaz update | grep -C $C "$GREP"

bash wiki-tests.sh Regression kaz rus update | grep -C $C "$GREP"

