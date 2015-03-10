#! /bin/bash

INPUTFILE=$1
BILDICTIONARY=$2

CURDIR=`dirname $0`
RULELEARNINGDIR="$CURDIR/../../rule-generalisation"

PAIR="en-es"

zcat $INPUTFILE | grep -v '^$' | grep -v -F '^$' |  sed 's:| *\^:| ':g | sed 's:\$ *|: |:g' | sed 's:\$ *\^: :g' | sed 's:\$_\^: :g' |  gzip > $INPUTFILE.clean.gz

zcat  $INPUTFILE.clean.gz | cut -f 2 -d '|'  | sed  's:^ *::' | sed  's_ *$__' | sed -r 's_ _\t_g' | sed -r 's:_: :g'  | apertium-apply-biling --biling $BILDICTIONARY > $INPUTFILE.clean.bildic

zcat $INPUTFILE.clean.gz  | paste -d '|' - $INPUTFILE.clean.bildic | python $RULELEARNINGDIR/processBilphrases.py --allow_all_alignments | gzip > $INPUTFILE.goodformat.gz

zcat $INPUTFILE.goodformat.gz | python $RULELEARNINGDIR/generateOneATFromBilphrases.py --tag_groups_file_name $RULELEARNINGDIR/taggroups_$PAIR --tag_sequences_file_name $RULELEARNINGDIR/tagsequences_$PAIR --closed_categories $CURDIR/markers | gzip >  $INPUTFILE.ats.gz

zcat $INPUTFILE.ats.gz | python $RULELEARNINGDIR/addGeneralisedLeftSide.py | LC_ALL=C sort -r | python $RULELEARNINGDIR/uniqSum.py | awk -F"|" '{print $2"|"$1"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' | sed 's_|\([0-9]\)_| \1_' |  LC_ALL=C sort -r | ${PYTHONHOME}python $RULELEARNINGDIR/removeExplicitEmptuTagsFromPatternTLandRest.py --emptyrestrictionsmatcheverything | awk -F"|" '{print $2"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' > $INPUTFILE.ats.prepared

apertium-gen-transfer-from-aligment-templates --input $INPUTFILE.ats.prepared --attributes $RULELEARNINGDIR/taggroups_$PAIR --generalise --nodoublecheckrestrictions --usediscardrule --emptyrestrictionsmatcheverything  > $INPUTFILE.rules.xml
