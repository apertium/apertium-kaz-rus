#! /bin/bash

ALIGNMENTSFILE="$1"
BILDICTIONARY=$2
RULELEARNINGDIR=$3
ENDSALIGNED=$4 #ignored at the moment
SAMESTRUCTURE=$5 #ignored at the moment
VARIANT=$6
EXTREMES_VARIANT=$7

#extract bilphrases
python $RULELEARNINGDIR/extractPhrases.py --sentences "$ALIGNMENTSFILE" --closed_categories ./markers --variant "$VARIANT" --extremes_variant "$EXTREMES_VARIANT" |  grep -v -F ' *' | grep -v -F '<sent>' | grep -v -F '<guio>'  | grep -F -v '<cm>' | grep  -v '<[rl]par>' | grep  -v '<[rl]quest>' | LC_ALL=C sort | LC_ALL=C uniq -c | sed 's:^ *::' | sed 's:<:| <:' 