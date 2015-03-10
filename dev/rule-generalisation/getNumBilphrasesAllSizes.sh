#! /bin/bash

DIR=$1
SL=$2
TL=$3

for SUFFIX in "" "-p40"; do

if [ -d "$DIR$SUFFIX" ]; then

pushd "$DIR$SUFFIX" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE/bilingualphrases > /dev/null

NUM_RULES=`zcat alignmentTemplatesPlusLemmas.withalllemmas.onlyslpos.filtered-1-count.$SL-$TL.gz | wc -l`

echo "$SIZE	$NUM_RULES"

popd > /dev/null

done

popd > /dev/null

fi
done