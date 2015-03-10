#! /bin/bash

DIR=$1
SL=$2
TL=$3

pushd "$DIR" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE > /dev/null

#echo "$SIZE"

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi

TRANSFERTOOLSDIR=/work/vmsanchez/rules/apertium-transfer-tools-generalisation/rule-generalisation

APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator
BEST_THRESHOLD=`cat result-${SL}-${TL} | tr '\t' ' ' | sed 's: [ ]*: :g' | cut -f 4 -d ' '`

#if [ "$BEST_THRESHOLD" == "0" ]; then
#	MIDDLENUM="1"
#else
#	MIDDLENUM=$BEST_THRESHOLD
#fi
MIDDLENUM=1

pushd test-$BEST_THRESHOLD-count > /dev/null

COVERAGE=`python $TRANSFERTOOLSDIR/summarizeReport.py  < report-rules-$SL-$TL-words | grep -F 'by rules:' | cut -f 2 -d '(' | cut -f 1 -d ')' | sed 's:%$::'`

echo "$SIZE	$COVERAGE"

popd > /dev/null

popd > /dev/null

done

popd > /dev/null