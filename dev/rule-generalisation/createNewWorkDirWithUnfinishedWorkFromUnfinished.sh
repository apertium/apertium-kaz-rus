#! /bin/bash

MYFULLPATH=`readlink -f $0`
CURDIR=`dirname $MYFULLPATH`

BILID=$1
SL=$2
TL=$3
SIZE=$4

PAIR="$SL-$TL"
BOXES_PER_SLOT=1
FILTERING_METHOD=proportion_correct_bilphrases_thresholdextendedrangerelaxdynamic1000above2
MYTMPDIR=/work/vmsanchez/rules/tmps-2unfinished

FULLEULERPATH="/home/vmsanchez/results/experiments-linear-l5-$SL-$TL/$BILID-unfinished/shuf$SIZE"

NEWEULERPATH="/home/vmsanchez/results/experiments-linear-l5-$SL-$TL/$BILID-unfinishedfromunfinished/shuf$SIZE"


mkdir -p $MYTMPDIR/$PAIR/$BILID/$SIZE/all
mkdir -p $MYTMPDIR/$PAIR/$BILID/$SIZE/original
mkdir -p $MYTMPDIR/$PAIR/$BILID/$SIZE/split

UNFININSHEDPARTS_F=`mktemp`

ssh vmsanchez@euler.iuii.ua.es "bash /home/vmsanchez/sources/apertium-transfer-tools-generalisation/rule-generalisation/getUnfinishedParts.sh $FULLEULERPATH $FILTERING_METHOD sepbythreshold " > $UNFININSHEDPARTS_F

scp vmsanchez@euler.iuii.ua.es:$FULLEULERPATH/generalisation-*.tar.gz $MYTMPDIR/$PAIR/$BILID/$SIZE/all/

for PART in `cat $UNFININSHEDPARTS_F` ; do
	mv $MYTMPDIR/$PAIR/$BILID/$SIZE/all/generalisation-$PART-*.tar.gz $MYTMPDIR/$PAIR/$BILID/$SIZE/original
done

pushd $MYTMPDIR/$PAIR/$BILID/$SIZE/original
	for FILE in *.tar.gz ; do
		tar xzf $FILE
	done
	
	pushd generalisation/ats
		TOTALBOXES=`ls | wc -l`
	popd
	
	TOTALPARTS=$((TOTALBOXES / BOXES_PER_SLOT))
	REMAINDER=$((TOTALBOXES % BOXES_PER_SLOT))
	if [ $REMAINDER -gt 0 ]; then
		TOTALPARTS=`expr $TOTALPARTS + 1`
	fi
	
	echo "$TOTALBOXES boxes. $TOTALPARTS parts"
popd

bash $CURDIR/reArrangeGeneralisation.sh $MYTMPDIR/$PAIR/$BILID/$SIZE/original/generalisation  $MYTMPDIR/$PAIR/$BILID/$SIZE/split $TOTALPARTS

ssh vmsanchez@euler.iuii.ua.es "mkdir -p $NEWEULERPATH; cp $FULLEULERPATH/generalisation-pre.tar.gz $NEWEULERPATH/"

pushd $MYTMPDIR/$PAIR/$BILID/$SIZE/split
	scp generalisation-*.tar.gz vmsanchez@euler.iuii.ua.es:$NEWEULERPATH
popd

rm -f $UNFININSHEDPARTS_F



