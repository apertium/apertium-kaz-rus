#! /bin/bash

INPUTFILE=$1
BILDICTIONARY=$2
RULELEARNINGDIR=$3
ENDSALIGNED=$4
SAMESTRUCTURE=$5
VARIANT=$6

WDIR=`dirname $1`

ENDSALIGNEDFLAG=""
if [ "$ENDSALIGNED" != "" ]; then
	ENDSALIGNEDFLAG="--ends_must_be_aligned"
fi

zcat $INPUTFILE |  grep -v -F '^*' | grep -v -F '^$' | grep -v -F '<sent>' | grep -v -F '<guio>'  | grep -F -v '<cm>' | grep  -v '<[rl]par>' | grep  -v '<[rl]quest>' |  sed 's:| *\^:| ':g | sed 's:\$ *|: |:g' | sed 's:\$ *\^: :g' | gzip > $INPUTFILE.clean.gz
zcat $INPUTFILE | sed 's:^[^|]*| ::' | LC_ALL=C sort | uniq -c | sed 's:^ *::' | sed 's:\^:| ^:'  |  grep -v -F '^*' | grep -v -F '^$' | grep -v -F '<sent>' | grep -v -F '<guio>' | grep -F -v '<cm>' | grep  -v '<[rl]par>' | grep  -v '<[rl]quest>' |  sed 's:| *\^:| ':g | sed 's:\$ *|: |:g' | sed 's:\$ *\^: :g' | gzip > $INPUTFILE.cleanuniq.gz

zcat  $INPUTFILE.cleanuniq.gz | cut -f 2 -d '|'  | sed  's:^ *::' | sed  's_ *$__' | sed -r 's_ _\t_g' | sed -r 's:_: :g'  | apertium-apply-biling --biling $BILDICTIONARY --withqueue > $INPUTFILE.cleanuniq.bildic
zcat  $INPUTFILE.clean.gz | cut -f 2 -d '|'  | sed  's:^ *::' | sed  's_ *$__' | sed -r 's_ _\t_g' | sed -r 's:_: :g'  | apertium-apply-biling --biling $BILDICTIONARY --withqueue  > $INPUTFILE.clean.bildic

#TODO: deal with empty TL tags: example: anar gets empty translation

STRUCTPARAMETER=""
if [ "$SAMESTRUCTURE" != "" ]; then
  zcat $INPUTFILE.cleanuniq.gz | paste -d '|' - $INPUTFILE.cleanuniq.bildic | python $RULELEARNINGDIR/processBilphrases.py --extract_structures --closed_categories ./markers $ENDSALIGNEDFLAG --variant "$VARIANT" | LC_ALL=C sort | uniq | gzip > $INPUTFILE.structures.gz
  STRUCTPARAMETER="--allowed_structures $INPUTFILE.structures.gz"
  zcat $INPUTFILE.clean.gz  | paste -d '|' - $INPUTFILE.clean.bildic | python $RULELEARNINGDIR/processBilphrases.py --closed_categories ./markers  $STRUCTPARAMETER  $ENDSALIGNEDFLAG --variant "$VARIANT" | LC_ALL=C sort | python $RULELEARNINGDIR/removeBilphraseConflictsWithWordId.py |  sed 's:^[^|]*| ::' | LC_ALL=C sort | LC_ALL=C uniq -c | sed 's:^ *::' | sed 's:<:| <:' | gzip
else
  zcat $INPUTFILE.cleanuniq.gz  | paste -d '|' - $INPUTFILE.cleanuniq.bildic | python $RULELEARNINGDIR/processBilphrases.py --closed_categories ./markers $ENDSALIGNEDFLAG $STRUCTPARAMETER --variant "$VARIANT" | gzip
fi


