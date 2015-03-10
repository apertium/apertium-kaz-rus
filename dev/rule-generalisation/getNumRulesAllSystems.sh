#! /bin/bash

DIR=$1
SL=$2
TL=$3

for SUFFIX in "" "-p40"; do

if [ -d "$DIR$SUFFIX" ]; then

pushd "$DIR$SUFFIX" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE/beamresult > /dev/null

#echo "$SIZE"

#RESULTTFILE=`find . -name 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove*' | head -n 1`

RESULTTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"

if [ -f "$RESULTTFILE" ]; then

NUM_RULES=`cat $RESULTTFILE | tail -n 1`

echo "$SIZE	$NUM_RULES"

fi

popd > /dev/null

done

popd > /dev/null

fi
done