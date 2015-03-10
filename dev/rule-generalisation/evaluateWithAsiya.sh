#! /bin/bash

SL=$1
TL=$2

SOURCE=$3
TARGET=$4
REF=$5

PARMETRIC=$6

CFGFILE=`mktemp`
EVALUATIONFILE=`mktemp`


#FULLSRC=`readlink -f $SOURCE`
#FULLTRG=`readlink -f $TARGET`
#FULLREF=`readlink -f $REF`

#ugly trick to avoid asiya cache

FULLSRC=`mktemp`
FULLTRG=`mktemp`
FULLREF=`mktemp`


APERTIUMEVALOOLS=/home/vmsanchez/rulesinteractive/apertium-eval-translator

if [ "$TL" == "es" -o "$TL" == "en" -o "$TL" == "fr" ]; then
METEOR_VARIANT="pa"
else
METEOR_VARIANT="ex"
fi
# 

PROGRAM1=""
PROGRAM2=""
PROGRAM3=""

if [ "$PARMETRIC" == "" ]; then
	METRIC="BLEU METEOR-$METEOR_VARIANT -TER"
	
	PROGRAM1="bleu"
	PROGRAM2="ter"
	PROGRAM3="meteor-$TL"
fi
	
if [ "$PARMETRIC" == "1" ]; then
	METRIC="BLEU"
	
	PROGRAM1="bleu"
fi

if [ "$PARMETRIC" == "2" ]; then
	METRIC="-TER"
	
	PROGRAM1="ter"
fi

if [ "$PARMETRIC" == "3" ]; then
	METRIC="METEOR-$METEOR_VARIANT"
	
	PROGRAM1="meteor-$TL"
fi

NOTOK=""
if [ "$SL" == "br" ]; then
	NOTOK="-no_tok"
fi


cat $SOURCE > $FULLSRC
cat $TARGET > $FULLTRG
cat $REF > $FULLREF


if [ "A" == "B" ]; then
#prepare Asiya cfg
echo "input=raw" >> $CFGFILE
echo "src=$FULLSRC" >> $CFGFILE
echo "sys=$FULLTRG" >> $CFGFILE
echo "ref=$FULLREF" >> $CFGFILE
if [ "$SL" == "br" ] ; then
echo "srclang=en" >> $CFGFILE
else
echo "srclang=$SL" >> $CFGFILE
fi
echo "srccase=ci" >> $CFGFILE
echo "trglang=$TL" >> $CFGFILE
echo "trgcase=ci">> $CFGFILE
echo "some_metrics=$METRIC" >> $CFGFILE

#run asiya and print output
/home/vmsanchez/rulesinteractive/asiya/bin/Asiya.pl $NOTOK -eval single  -metric_set some_metrics  $CFGFILE > $EVALUATIONFILE
BLEU=`head -n 3 $EVALUATIONFILE | tail -n 1 | sed 's: [ ]*: :g' | cut -f 3 -d ' '`
fi

BLEU=`$APERTIUMEVALOOLS/$PROGRAM1.sh $FULLSRC $FULLREF $FULLTRG`

if [ "$PARMETRIC" == "" ]; then
#TER=`head -n 3 $EVALUATIONFILE | tail -n 1 | sed 's: [ ]*: :g' | cut -f 4 -d ' '`
#METEOR=`head -n 3 $EVALUATIONFILE | tail -n 1 | sed 's: [ ]*: :g' | cut -f 5 -d ' '`
TER=`$APERTIUMEVALOOLS/$PROGRAM2.sh $FULLSRC $FULLREF $FULLTRG`
METEOR=`$APERTIUMEVALOOLS/$PROGRAM3.sh $FULLSRC $FULLREF $FULLTRG`
echo "$BLEU	$TER	$METEOR"

else
echo "$BLEU"
fi


rm $FULLSRC $FULLTRG $FULLREF
rm $CFGFILE $EVALUATIONFILE
