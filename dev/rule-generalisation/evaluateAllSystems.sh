#! /bin/bash

DIR=$1
SL=$2
TL=$3

for SUFFIX in "" "-p40"; do

pushd "$DIR$SUFFIX" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE/beamresult > /dev/null

#echo "$SIZE"

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi

APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator


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

rm -f asiya.cfg

TMPSRC=`mktemp`
TMPTRG=`mktemp`
TMPREF=`mktemp`



cat source > $TMPSRC
cat translation_learnedrules > $TMPTRG
cat reference > $TMPREF


if [ ! -f bleu.learnedrules ]; then
	$APERTIUMEVALOOLS/bleu.sh $TMPSRC $TMPREF $TMPTRG > bleu.learnedrules &
fi

if [ ! -f ter.learnedrules ]; then
	$APERTIUMEVALOOLS/ter.sh $TMPSRC $TMPREF $TMPTRG > ter.learnedrules &
fi

if [ ! -f meteor.learnedrules ]; then
	$APERTIUMEVALOOLS/meteor-$TL.sh $TMPSRC $TMPREF $TMPTRG > meteor.learnedrules &
fi

wait


BLEU=`cat bleu.learnedrules`
TER=`cat ter.learnedrules`
METEOR=`cat meteor.learnedrules`

echo "$SIZE	$BLEU	$TER	$METEOR"

rm -f $TMPSRC $TMPTRG $TMPREF
fi

popd > /dev/null

popd > /dev/null

done

popd > /dev/null

done