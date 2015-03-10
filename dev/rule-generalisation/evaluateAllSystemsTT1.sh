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


APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator
BEST_THRESHOLD=`cat result-${SL}-${TL} | tr '\t' ' ' | sed 's: [ ]*: :g' | cut -f 4 -d ' '`

#if [ "$BEST_THRESHOLD" == "0" ]; then
#	MIDDLENUM="1"
#else
#	MIDDLENUM=$BEST_THRESHOLD
#fi
MIDDLENUM=1

pushd test-$BEST_THRESHOLD-count > /dev/null

rm -f asiya.cfg

TMPSRC=`mktemp`
TMPTRG=`mktemp`
TMPREF=`mktemp`

cat test.${SL}-${TL}.source > $TMPSRC
cat test.${SL}-${TL}.translation > $TMPTRG
cat test.${SL}-${TL}.reference > $TMPREF

if [ "A" == "B" ] ; then
#prepare Asiya cfg
echo "input=raw" >> asiya.cfg
echo "src=$TMPSRC" >> asiya.cfg
echo "sys=$TMPTRG" >> asiya.cfg
echo "ref=$TMPREF" >> asiya.cfg
if [ "$SL" == "br" ] ; then
echo "srclang=en" >> asiya.cfg
else
echo "srclang=$SL" >> asiya.cfg
fi
echo "srccase=ci" >> asiya.cfg
echo "trglang=$TL" >> asiya.cfg
echo "trgcase=ci">> asiya.cfg
echo "some_metrics=BLEU METEOR-$METEOR_VARIANT -TER" >> asiya.cfg
fi

rm -f asiyaevaluation
if [ "A" == "B" ] ; then
#run asiya and print output
/home/vmsanchez/rulesinteractive/asiya/bin/Asiya.pl -eval single  -metric_set some_metrics  asiya.cfg > asiyaevaluation
BLEU=`head -n 3 asiyaevaluation | tail -n 1 | sed 's: [ ]*: :g' | cut -f 3 -d ' '`
TER=`head -n 3 asiyaevaluation | tail -n 1 | sed 's: [ ]*: :g' | cut -f 4 -d ' '`
METEOR=`head -n 3 asiyaevaluation | tail -n 1 | sed 's: [ ]*: :g' | cut -f 5 -d ' '`

fi
BLEU=`$APERTIUMEVALOOLS/bleu.sh $TMPSRC $TMPREF $TMPTRG`
TER=`$APERTIUMEVALOOLS/ter.sh $TMPSRC $TMPREF $TMPTRG`
METEOR=`$APERTIUMEVALOOLS/meteor-$TL.sh $TMPSRC $TMPREF $TMPTRG`

echo "$SIZE	$BLEU	$TER	$METEOR"



rm -f $TMPSRC $TMPTRG $TMPREF

popd > /dev/null

popd > /dev/null

done

popd > /dev/null