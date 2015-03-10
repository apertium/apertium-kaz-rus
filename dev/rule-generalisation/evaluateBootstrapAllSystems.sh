#! /bin/bash

DIR=$1
DIRTT1=$2
SL=$3
TL=$4

APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator
NTIMES=1000

pushd "$DIR" > /dev/null

for SIZE in `ls | sort -n` ; do 

pushd $SIZE/beamresult > /dev/null

#echo "$SIZE"

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi

#RESULTFILE=`find . -name 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove*' | head -n 1` 
#ABOVENUMBER=`echo "$RESULTFILE" | sed 's:.*result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove::'`

RESULTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"

if [ -f "$RESULTFILE" ]; then

BEST_THRESHOLD=`cat $RESULTFILE | tail -n 2 | head -n 1`
NUM_RULES=`cat $RESULTFILE | tail -n 1`

#if [ "$BEST_THRESHOLD" == "0" ]; then
#	MIDDLENUM="1"
#else
#	MIDDLENUM=$BEST_THRESHOLD
#fi
MIDDLENUM=1

pushd tuning-proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2-${BEST_THRESHOLD}-${MIDDLENUM}-${BEST_THRESHOLD}-subrules/queries/test-f-$BEST_THRESHOLD/experiment/evaluation > /dev/null


#find tt1.0 evaluation file

BESTTHRESHOLDTT1=`cat $DIRTT1/$SIZE/result-${SL}-${TL} | tr '\t' ' ' | sed 's: [ ]*: :g' | cut -f 4 -d ' '`
TRANSLATION_BASE=$DIRTT1/$SIZE/test-$BESTTHRESHOLDTT1-count/test.${SL}-${TL}.translation


#run paired bootsrap with 3 metrics
if [ ! -f "./paired-bootstrap-tt1.BLEU" ]; then
	$APERTIUMEVALOOLS/mteval_by_bootstrap_resampling.pl -source source -test translation_learnedrules -testb $TRANSLATION_BASE -ref reference -times $NTIMES -eval $APERTIUMEVALOOLS/bleu.sh  > ./paired-bootstrap-tt1.BLEU &
fi


if [ ! -f "./paired-bootstrap-tt1.TER" ]; then
	$APERTIUMEVALOOLS/mteval_by_bootstrap_resampling.pl -source source -test translation_learnedrules -testb $TRANSLATION_BASE -ref reference -times $NTIMES -eval $APERTIUMEVALOOLS/ter.sh  > ./paired-bootstrap-tt1.TER &
fi


if [ ! -f "./paired-bootstrap-tt1.METEOR" ]; then
	$APERTIUMEVALOOLS/mteval_by_bootstrap_resampling.pl -source source -test translation_learnedrules -testb $TRANSLATION_BASE -ref reference -times $NTIMES -eval $APERTIUMEVALOOLS/meteor-$TL.sh  > ./paired-bootstrap-tt1.METEOR &
fi


wait


popd > /dev/null

fi

popd > /dev/null

done

popd > /dev/null