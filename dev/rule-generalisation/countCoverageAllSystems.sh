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

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi

TRANSFERTOOLSDIR=/work/vmsanchez/rules/apertium-transfer-tools-generalisation/rule-generalisation

VALIDDIR=false
if [ -f 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2' ]; then
	RESULTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"
	FILTERINGNAME="proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"
	VALIDDIR=true
else

	NUMBERSFILE=`mktemp`
	find . -name 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove*' | sed 's:.*result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove::' > $NUMBERSFILE
	#we like the lowest number
	ABOVENUMBER=`cat $NUMBERSFILE | sort -n | head -n 1`
	RESULTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove$ABOVENUMBER"
	FILTERINGNAME="proportion_correct_bilphrases_thresholdextendedrangerelaxabove$ABOVENUMBER"
	rm -f $NUMBERSFILE
fi

if [ $VALIDDIR == true ]; then

BEST_THRESHOLD=`cat $RESULTFILE | tail -n 2 | head -n 1`
NUM_RULES=`cat $RESULTFILE | tail -n 1`

#if [ "$BEST_THRESHOLD" == "0" ]; then
#	MIDDLENUM="1"
#else
#	MIDDLENUM=$BEST_THRESHOLD
#fi
MIDDLENUM=1

echo "Evaluating $SL-$TL $FILTERINGNAME" >&2

pushd tuning-$FILTERINGNAME-${BEST_THRESHOLD}-${MIDDLENUM}-${BEST_THRESHOLD}-subrules/queries/test-f-$BEST_THRESHOLD/experiment/evaluation > /dev/null

COVERAGE=`python $TRANSFERTOOLSDIR/addWordInforToReport.py  < report_rules | python $TRANSFERTOOLSDIR/summarizeReport.py | grep -F 'by rules:' | cut -f 2 -d '(' | cut -f 1 -d ')' | sed 's:%$::'`


echo "$SIZE	$COVERAGE"

popd > /dev/null

fi

popd > /dev/null

done

popd > /dev/null

fi

done