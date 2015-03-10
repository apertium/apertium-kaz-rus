#! /bin/bash

SOURCE_DIR="$1"

PAIR="$2"
BILID="$3"
SIZE="$4"



scp $SOURCE_DIR/alignmentTemplatesPlusLemmas.withalllemmas.onlyslpos.filtered-1-count.$PAIR.gz euler.iuii.ua.es:/home/vmsanchez/data/input/$PAIR/$BILID/shuf${SIZE}l5.alignmentTemplatesPlusLemmas.withalllemmas.onlyslpos.filtered-1-count.$PAIR.gz

scp $SOURCE_DIR/alignments.$PAIR.gz.toBeam.gz  euler.iuii.ua.es:/home/vmsanchez/data/input/$PAIR/$BILID/shuf${SIZE}l5.sentences.$PAIR.gz

L1=`echo "$PAIR" | cut -f 1 -d '-'`
L2=`echo "$PAIR" | cut -f 2 -d '-'`

#copy dev corpus
if [ -f $SOURCE_DIR/devcorpus.$SIZE.$L1 -a -f $SOURCE_DIR/devcorpus.$SIZE.$L2 ]; then
	scp $SOURCE_DIR/devcorpus.$SIZE.$L1 $SOURCE_DIR/devcorpus.$SIZE.$L2 euler.iuii.ua.es:/home/vmsanchez/data/input/$PAIR/$BILID/
fi

#copy attribute change counts
if [ -f $SOURCE_DIR/attributesChange.${L1}-${L2}  ]; then
	scp $SOURCE_DIR/attributesChange.${L1}-${L2} euler.iuii.ua.es:/home/vmsanchez/data/input/$PAIR/$BILID/
fi