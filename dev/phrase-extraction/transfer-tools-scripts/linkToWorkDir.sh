#!/bin/bash

WORKDIR=$1

CURDIR=`pwd`

for file in `ls`; do
	ln -s $CURDIR/$file $WORKDIR/$file
done
