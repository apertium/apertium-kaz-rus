#! /bin/bash

DIR=$1
SL=$2
TL=$3

for SUFFIX in "" "-p40"; do

pushd "$DIR$SUFFIX" > /dev/null

for SIZE in `ls | sort -n` ; do 

if [ -d "$DIR$SUFFIX" ]; then

pushd $SIZE/beamresult > /dev/null

#echo "$SIZE"

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi

TRANSFERTOOLSDIR=/work/vmsanchez/rules/apertium-transfer-tools-generalisation/rule-generalisation
APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator

if [ -f 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2' ]; then
	RESULTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"
	FILTERINGNAME="proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2"
else

	NUMBERSFILE=`mktemp`
	find . -name 'result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove*' | sed 's:.*result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove::' > $NUMBERSFILE
	#we like the lowest number
	ABOVENUMBER=`cat $NUMBERSFILE | sort -n | head -n 1`
	RESULTFILE="result_proportion_correct_bilphrases_thresholdextendedrangerelaxabove$ABOVENUMBER"
	FILTERINGNAME="proportion_correct_bilphrases_thresholdextendedrangerelaxabove$ABOVENUMBER"
	rm -f $NUMBERSFILE
fi


BEST_THRESHOLD=`cat $RESULTFILE | tail -n 2 | head -n 1`
NUM_RULES=`cat $RESULTFILE | tail -n 1`

if [ "$FILTERINGNAME" == "proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2" ]; then

echo "Counting pruning $SL-$TL $FILTERINGNAME" >&2

pushd .. > /dev/null

if [ ! -d filtering-$FILTERINGNAME  ]; then

BILID=`basename $DIR`

#download filtering
scp euler.iuii.ua.es:/home/vmsanchez/results/experiments-linear-l5-${SL}-${TL}/$BILID/shuf$SIZE/filtering-$FILTERINGNAME-*.tar.gz ./
for file in `ls filtering-$FILTERINGNAME-*.tar.gz`; do
    tar xzf $file
done

fi

pushd filtering-$FILTERINGNAME > /dev/null

if [ ! -f discardingstatistics ]; then

find ./debug -name '*-f-0.result.debug.gz' | while read FILE ; do
	THETA=`zcat $FILE | grep -F 'For limit=' | cut -f 3 -d '='`
	NUMBER=`basename $FILE -f-0.result.debug.gz`
	TOTALATS=`zcat ./ats/$NUMBER.ats.gz | wc -l`
	if [ "$THETA" == "-1" ]; then
		ALLOWEDATS="0"
	elif [ "$THETA" == "2" ]; then
		ALLOWEDATS="$TOTALATS"
	else
		ALLOWEDATS=`zcat ./ats/$NUMBER.ats.gz | python $TRANSFERTOOLSDIR/filterAlignmentTemplates.py --min_count $THETA | wc -l`
	fi
	
	echo "$NUMBER	$THETA	$ALLOWEDATS	$TOTALATS" >> discardingstatistics
done
fi

AVERAGECONSIDERED=`cat discardingstatistics | grep -v '	0$' | awk '{sum+=$3/$4; rows+=1;} END {print sum/rows;}'`

echo "$SIZE	$AVERAGECONSIDERED"

popd > /dev/null


popd > /dev/null

fi


popd > /dev/null

done

popd > /dev/null

fi
done