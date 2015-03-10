#! /bin/bash

MASTER_GENERALISATION_DIR=$1
OUTPUT_DIR=$2
NUM_PARTS=$3

pushd $MASTER_GENERALISATION_DIR

BOXIDSSORTEDBYLENGTH=`mktemp`

pushd ats
ls --sort=size | sed 's:\.ats\.gz::' > $BOXIDSSORTEDBYLENGTH
popd

COUNTER=0
while read ID ; do
	PART=`expr $COUNTER % $NUM_PARTS`
	
	#copy stuff
	mkdir -p $OUTPUT_DIR/result_$PART/generalisation/ats
	mkdir -p $OUTPUT_DIR/result_$PART/generalisation/debug
	mkdir -p $OUTPUT_DIR/result_$PART/generalisation/newbilphrases
	
	cp ats/$ID.ats.gz $OUTPUT_DIR/result_$PART/generalisation/ats
	cp debug/debug-generalisation-$ID.gz $OUTPUT_DIR/result_$PART/generalisation/debug
	cp newbilphrases/$ID.bilphrases.gz $OUTPUT_DIR/result_$PART/generalisation/newbilphrases
	
	COUNTER=`expr $COUNTER + 1`
	
done < $BOXIDSSORTEDBYLENGTH


for PART in `seq $NUM_PARTS` ; do
	PART_MINUS_ONE=`expr $PART - 1 `
	cp boxesindex boxesofnewdata.sorted.bylength.* finalboxesindex $OUTPUT_DIR/result_$PART_MINUS_ONE/generalisation
done

rm -f $BOXIDSSORTEDBYLENGTH

popd


pushd $OUTPUT_DIR
for PART in `seq $NUM_PARTS` ; do
	PART_MINUS_ONE=`expr $PART - 1 ` 
	pushd result_$PART_MINUS_ONE
	tar czf generalisation-$PART-$NUM_PARTS.tar.gz generalisation
	mv generalisation-$PART-$NUM_PARTS.tar.gz ../
	popd
done
popd
