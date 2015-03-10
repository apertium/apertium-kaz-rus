#! /bin/bash

DIR=$1
SL=$2
TL=$3

pushd "$DIR" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE > /dev/null

NUM_RULES=`cat result-${SL}-${TL} | tr '\t' ' ' | sed 's: [ ]*: :g' | cut -f 3 -d ' '`

echo "$SIZE	$NUM_RULES"

popd > /dev/null

done

popd > /dev/null