#! /bin/bash

CURDIR=`dirname $0`

#shflags
. $CURDIR/rule-generalisation/shflags

DEFINE_string 'source_language' 'en' 'source language language' 's'
DEFINE_string 'target_language' 'es' 'target language' 't'
DEFINE_string 'corpus' '' 'File containing the GF alignments (must be gzipped)' 'c'
DEFINE_string 'bilingual_dictionary' '' 'Binary bilingual dictionary file' 'b'

#process parameters
FLAGS "$@" || exit $?
eval set -- "${FLAGS_ARGV}"

SL=${FLAGS_source_language}
TL=${FLAGS_target_language}
PAIR="${SL}-${TL}"

INPUTFILE=${FLAGS_corpus}
BILDICTIONARY=${FLAGS_bilingual_dictionary}

RULELEARNINGDIR="$CURDIR/rule-generalisation"


zcat $INPUTFILE | grep -v '^$' | grep -v -F '^$' |  sed 's:| *\^:| ':g | sed 's:\$ *|: |:g' | sed 's:\$ *\^: :g' | sed 's:\$_\^: :g' |  gzip > $INPUTFILE.clean.gz

zcat  $INPUTFILE.clean.gz | cut -f 2 -d '|'  | sed  's:^ *::' | sed  's_ *$__' | sed -r 's_ _\t_g' | sed -r 's:_: :g'  | apertium-apply-biling --biling $BILDICTIONARY > $INPUTFILE.clean.bildic

zcat $INPUTFILE.clean.gz  | paste -d '|' - $INPUTFILE.clean.bildic | python $RULELEARNINGDIR/processBilphrases.py --allow_all_alignments | gzip > $INPUTFILE.goodformat.gz

zcat $INPUTFILE.goodformat.gz | python $RULELEARNINGDIR/generateOneATFromBilphrases.py --tag_groups_file_name $RULELEARNINGDIR/taggroups_$PAIR --tag_sequences_file_name $RULELEARNINGDIR/tagsequences_$PAIR --closed_categories $CURDIR/phrase-extraction/transfer-tools-scripts/markers 2> $INPUTFILE.ats.errors | gzip >  $INPUTFILE.ats.gz
gzip $INPUTFILE.ats.errors

zcat $INPUTFILE.ats.gz | python $RULELEARNINGDIR/addGeneralisedLeftSide.py | LC_ALL=C sort -r | python $RULELEARNINGDIR/uniqSum.py | awk -F"|" '{print $2"|"$1"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' | sed 's_|\([0-9]\)_| \1_' |  LC_ALL=C sort -r | ${PYTHONHOME}python $RULELEARNINGDIR/removeExplicitEmptuTagsFromPatternTLandRest.py --emptyrestrictionsmatcheverything | awk -F"|" '{print $2"|"$3"|"$4"|"$5"|"$6}' | sed 's_^ __' > $INPUTFILE.ats.prepared

apertium-gen-transfer-from-aligment-templates --input $INPUTFILE.ats.prepared --attributes $RULELEARNINGDIR/taggroups_$PAIR --generalise --nodoublecheckrestrictions --usediscardrule --emptyrestrictionsmatcheverything  > $INPUTFILE.rules.xml
